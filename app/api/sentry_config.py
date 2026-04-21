"""Sentry error tracking configuration."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from api.logging_config import get_logger
from config import get_settings

settings = get_settings()
logger = get_logger()


def init_sentry() -> None:
    """Initialize Sentry if DSN is configured."""
    if not settings.sentry_dsn:
        logger.debug("sentry_disabled_no_dsn")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[
            FastApiIntegration(transaction_style="url"),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
    logger.info("sentry_initialized", environment=settings.environment)


def capture_exception(exc: Exception, **kwargs) -> None:
    """Capture an exception with optional extra context."""
    sentry_sdk.capture_exception(exc)
    logger.error("exception_captured", error=str(exc), **kwargs)


def set_user_context(user_id: str, email: str | None = None) -> None:
    """Set authenticated user context for Sentry."""
    sentry_sdk.set_user({"id": user_id, "email": email})


def add_breadcrumb(message: str, category: str = "custom", **kwargs) -> None:
    """Add a breadcrumb for error debugging."""
    sentry_sdk.add_breadcrumb(message=message, category=category, data=kwargs)