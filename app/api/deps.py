import time
import uuid

import httpx
import structlog
from config import get_settings
from db.client import get_supabase_client
from fastapi import Header, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import BaseModel

settings = get_settings()
logger = structlog.get_logger()


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str


# Custom cached getter to avoid lru_cache issue with async
_jwks_cache = {"data": None, "expires_at": 0}
JWKS_TTL_SECONDS = 3600  # 1 hour


async def get_jwks() -> dict:
    """Fetch JWKS from Supabase with caching (1 hour TTL)."""
    current_time = time.time()
    if _jwks_cache["data"] and _jwks_cache["expires_at"] > current_time:
        return _jwks_cache["data"]

    async with httpx.AsyncClient(timeout=10.0) as client:
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        response = await client.get(jwks_url)
        response.raise_for_status()
        jwks = response.json()

    _jwks_cache["data"] = jwks
    _jwks_cache["expires_at"] = current_time + JWKS_TTL_SECONDS
    logger.info("jwks_fetched", cached=False)
    return jwks


async def decode_token(token: str) -> dict:
    try:
        jwks = await get_jwks()

        unverified_header = jwt.get_unverified_header(token)

        kid = unverified_header.get("kid")
        matching_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                matching_key = key
                break

        if not matching_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
            )

        payload = jwt.decode(
            token,
            matching_key,
            algorithms=["ES256", "RS256"],
            options={"verify_aud": False},
            issuer=f"{settings.supabase_url}/auth/v1",
        )
        return payload
    except JWTError as e:
        logger.warning("auth_decode_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )


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

    payload = await decode_token(token)

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        )

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    supabase = await get_supabase_client()

    response = supabase.table("users").select("*").eq("id", str(user_id)).execute()

    if not response.data:
        logger.warning("auth_user_not_found", user_id=str(user_id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user_data = response.data[0]

    # Store user data in request state for reuse in routes
    request.state.user_data = user_data

    return CurrentUser(id=user_id, email=user_data.get("email", ""))
