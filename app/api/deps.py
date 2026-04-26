from __future__ import annotations

import time
import uuid
from typing import Annotated

import httpx
import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import BaseModel

from config import get_settings
from db.client import execute_single

settings = get_settings()
logger = structlog.get_logger()

CACHE_TTL_SECONDS = 3600

_jwks_cache: dict | None = None
_jwks_expires_at: float = 0


async def get_jwks() -> dict:
    """Fetch JWKS from Cognito with caching (1 hour TTL)."""
    global _jwks_cache, _jwks_expires_at

    current_time = time.time()
    if _jwks_cache is not None and _jwks_expires_at > current_time:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.cognito_jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_expires_at = current_time + CACHE_TTL_SECONDS
        logger.info("cognito_jwks_fetched", url=settings.cognito_jwks_url)

    return _jwks_cache


async def decode_token(token: str) -> dict:
    """Decode and validate Cognito JWT token."""
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
            options={"verify_aud": False},
            issuer=settings.cognito_issuer,
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
    """Get current authenticated user from Cognito JWT token.

    On first login, automatically creates user record in Aurora if not exists.
    """
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

    email = payload.get("email", "")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email claim",
        )

    user = await _get_or_create_user(user_id, email)

    request.state.user_data = user

    return CurrentUser(id=user_id, email=email)


async def _get_or_create_user(user_id: uuid.UUID, email: str) -> dict:
    """Get user from Aurora or create on first login."""
    user = await execute_single(
        "SELECT * FROM users WHERE id = $1",
        str(user_id),
    )

    if user is None:
        logger.info("auth_first_login", user_id=str(user_id), email=email)
        await execute_single(
            "INSERT INTO users (id, email, created_at) VALUES ($1, $2, NOW())",
            str(user_id),
            email,
        )
        user = await execute_single(
            "SELECT * FROM users WHERE id = $1",
            str(user_id),
        )

    if user is None:
        raise RuntimeError(f"Failed to create or retrieve user {user_id}")

    return dict(user)


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str
