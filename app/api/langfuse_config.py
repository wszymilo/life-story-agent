"""LangFuse LLM tracing configuration: trace creation, scoring, and decorator re-export."""

from langfuse import Langfuse

__all__ = ["init_langfuse", "get_langfuse", "start_trace", "update_trace", "log_score"]

from api.logging_config import get_logger
from config import get_settings

settings = get_settings()
logger = get_logger()

_langfuse_client: Langfuse | None = None


def init_langfuse() -> Langfuse | None:
    """Initialize Langfuse client if keys are configured."""
    global _langfuse_client

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.debug("langfuse_disabled_no_keys")
        return None

    _langfuse_client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_base_url,
    )
    logger.info("langfuse_initialized")
    return _langfuse_client


def get_langfuse() -> Langfuse | None:
    """Get the initialized Langfuse client."""
    return _langfuse_client


def start_trace(name: str, user_id: str | None = None, metadata: dict | None = None) -> str | None:
    """Create a new LangFuse trace and return its ID.

    Returns the trace_id or None if LangFuse is not configured.
    """
    if not _langfuse_client:
        return None

    try:
        trace = _langfuse_client.trace(
            name=name,
            user_id=user_id,
            metadata=metadata or {},
        )
        trace_id = str(trace.id)
        logger.debug("langfuse_trace_started", trace_id=trace_id, name=name)
        return trace_id
    except Exception as e:
        logger.warning("langfuse_trace_failed", error=str(e))
        return None


def update_trace(
    trace_id: str,
    metadata: dict | None = None,
    status: str | None = None,
) -> None:
    """Update trace metadata (e.g., on session completion)."""
    if not _langfuse_client:
        return

    try:
        meta = metadata or {}
        if status:
            meta["status"] = status
        _langfuse_client.trace(
            id=trace_id,
            metadata=meta,
        )
        logger.debug("langfuse_trace_updated", trace_id=trace_id, status=status)
    except Exception as e:
        logger.warning("langfuse_trace_update_failed", error=str(e))


def log_score(
    trace_id: str,
    name: str,
    value: float,
    comment: str | None = None,
) -> None:
    """Attach an evaluation score to a LangFuse trace."""
    if not _langfuse_client:
        return

    try:
        _langfuse_client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
        )
        logger.debug("langfuse_score_logged", trace_id=trace_id, name=name, value=value)
    except Exception as e:
        logger.warning("langfuse_score_failed", error=str(e))
