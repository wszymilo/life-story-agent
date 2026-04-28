import json
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, status
from structlog import get_logger

logger = get_logger()

_firebase_app: firebase_admin.App | None = None


def init_firebase(credentials_json: str | None = None) -> None:
    global _firebase_app
    if _firebase_app is not None:
        return

    if not credentials_json:
        logger.warning("firebase_credentials not configured, skipping initialization")
        return

    try:
        cred_dict = json.loads(credentials_json)
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("firebase_initialized", project_id=cred_dict.get("project_id"))
    except json.JSONDecodeError as e:
        logger.error("firebase_invalid_credentials_json", error=str(e))
        raise ValueError("Invalid Firebase credentials JSON")
    except Exception as e:
        logger.error("firebase_init_failed", error=str(e))
        raise


def verify_firebase_token(id_token: str) -> dict[str, Any]:
    if _firebase_app is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase not initialized",
        )

    try:
        decoded = auth.verify_id_token(id_token, app=_firebase_app)
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except auth.InvalidIdTokenError as e:
        logger.warning("firebase_invalid_token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        logger.error("firebase_token_verification_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


def get_firebase_user_by_email(email: str) -> auth.UserRecord | None:
    if _firebase_app is None:
        return None
    try:
        return auth.get_user_by_email(email, app=_firebase_app)
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        logger.error("firebase_get_user_by_email_failed", error=str(e))
        return None


def create_firebase_user(email: str) -> auth.UserRecord:
    if _firebase_app is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase not initialized",
        )
    try:
        user = auth.create_user(email=email, app=_firebase_app)
        logger.info("firebase_user_created", uid=user.uid, email=email)
        return user
    except Exception as e:
        logger.error("firebase_create_user_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )