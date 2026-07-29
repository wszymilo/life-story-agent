import structlog
from fastapi import Header, HTTPException, Request, status
from pydantic import BaseModel

from config import get_settings
from db.repositories import UserRepository
from services.firebase_auth import verify_firebase_token, get_firebase_user_by_email, create_firebase_user

settings = get_settings()
logger = structlog.get_logger()


class CurrentUser(BaseModel):
    id: str
    email: str


async def get_current_user(
    request: Request, authorization: str = Header(default=None)
) -> CurrentUser:
    if not authorization:
        logger.warning("auth_missing_header", path="/api/users/me")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        logger.warning("auth_invalid_format", path="/api/users/me")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    firebase_payload = verify_firebase_token(token)

    email = firebase_payload.get("email")
    firebase_uid = firebase_payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email claim",
        )

    pool = request.app.state.pool
    repo = UserRepository(pool)

    user = await repo.fetch_by_email(email)

    if not user:
        user_record = get_firebase_user_by_email(email)
        if not user_record:
            user_record = create_firebase_user(email)

        user = await repo.upsert(firebase_uid, email)

    request.state.user_data = user

    return CurrentUser(id=user["id"], email=user.get("email", ""))
