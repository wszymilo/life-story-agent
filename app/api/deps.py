import structlog
from config import get_settings
from db.client import get_supabase_client
from fastapi import Header, HTTPException, Request, status
from pydantic import BaseModel

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

    supabase = await get_supabase_client()

    response = supabase.table("users").select("*").eq("email", email).execute()

    if not response.data:
        user_record = get_firebase_user_by_email(email)
        if not user_record:
            user_record = create_firebase_user(email)

        response = supabase.table("users").insert({
            "id": firebase_uid,
            "email": email,
            "preferred_language": "pl",
        }).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

    user_data = response.data[0]

    request.state.user_data = user_data

    return CurrentUser(id=user_data["id"], email=user_data.get("email", ""))