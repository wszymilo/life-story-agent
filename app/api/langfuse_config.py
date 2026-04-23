"""LangFuse LLM tracing configuration."""

from langfuse import Langfuse

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


def log_generation(
    prompt: str,
    completion: str,
    model: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Log an LLM generation to Langfuse."""
    if not _langfuse_client:
        return

    try:
        meta = {**(metadata or {}), "user_id": user_id}
        with _langfuse_client.start_as_current_observation(
            name="llm_generation",
            as_type="generation",
            input={"prompt": prompt[:500]},
            output={"completion": completion[:500]},
            model=model,
            metadata=meta,
        ):
            pass
    except Exception as e:
        logger.warning("langfuse_log_failed", error=str(e))


