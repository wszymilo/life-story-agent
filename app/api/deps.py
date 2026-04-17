import uuid

import httpx
from config import get_settings
from db.client import get_supabase_client
from fastapi import Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel

settings = get_settings()


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str


async def get_jwks() -> dict:
    async with httpx.AsyncClient() as client:
        jwks_url = f"{settings.supabase_url}/.well-known/jwks.json"
        response = await client.get(jwks_url)
        response.raise_for_status()
        return response.json()


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
            algorithms=["RS256"],
            audience=settings.supabase_anon_key,
            issuer=f"{settings.supabase_url}/auth/v1",
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )


async def get_current_user(authorization: str = Header(default=None)) -> CurrentUser:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
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

    response = await supabase.table("users").select("*").eq("id", str(user_id)).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user_data = response.data[0]

    return CurrentUser(id=user_id, email=user_data.get("email", ""))
