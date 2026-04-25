"""LangFuse LLM tracing configuration: trace creation, scoring, and decorator re-export.

Compatible with LangFuse Python SDK v4.x (OpenTelemetry-based).
"""

from datetime import datetime, timezone
from typing import Any

from langfuse import Langfuse
from langfuse.api.ingestion.types import IngestionEvent_TraceCreate, TraceBody

__all__ = [
    "init_langfuse",
    "get_langfuse",
    "start_trace",
    "update_trace",
    "log_score",
    "report_generation_usage",
]

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


def start_trace(
    name: str,
    user_id: str | None = None,
    session_id: str | None = None,
    metadata: dict | None = None,
) -> str | None:
    """Create a new LangFuse trace via legacy ingestion API and return its ID.

    The v4 SDK is OpenTelemetry-based and no longer has client.trace().
    We use the legacy ingestion endpoint to create the trace skeleton with
    user_id and session_id, then attach observations via @observe(langfuse_trace_id=...).

    Returns the trace_id or None if LangFuse is not configured.
    """
    if not _langfuse_client:
        return None

    try:
        trace_id = _langfuse_client.create_trace_id()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        event = IngestionEvent_TraceCreate(
            id=_langfuse_client.create_trace_id(),
            timestamp=timestamp,
            body=TraceBody(
                id=trace_id,
                timestamp=timestamp,
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
            ),
        )

        _langfuse_client.api.ingestion.batch(batch=[event])
        logger.debug("langfuse_trace_started", trace_id=trace_id, name=name, user_id=user_id, session_id=session_id)
        return trace_id
    except Exception as e:
        logger.warning("langfuse_trace_failed", error=str(e))
        return None


def update_trace(
    trace_id: str,
    metadata: dict | None = None,
    status: str | None = None,
) -> None:
    """Update trace metadata (e.g., on session completion).

    NOTE: LangFuse v4 SDK (OpenTelemetry-based) does not support trace updates
    via the legacy ingestion API. This function is now a no-op for backward
    compatibility. Trace metadata should be set at creation time via start_trace().
    """
    if not _langfuse_client:
        return

    logger.debug(
        "langfuse_trace_update_skipped_v4",
        trace_id=trace_id,
        status=status,
        metadata=metadata,
    )


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
        _langfuse_client.create_score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
        )
        logger.debug("langfuse_score_logged", trace_id=trace_id, name=name, value=value)
    except Exception as e:
        logger.warning("langfuse_score_failed", error=str(e))


def report_generation_usage(
    model: str,
    usage: dict[str, int] | None = None,
) -> None:
    """Report token usage for the current LLM generation to LangFuse.

    Must be called from within an @observe() decorated function (or child)
    while the generation span is still active.  LangFuse calculates costs
    server-side when model + usage_details are provided.

    Args:
        model: Model name (e.g. "gpt-4o-mini", "whisper-1").
        usage: Dict with token counts. Expected keys:
            - "prompt_tokens" or "input"
            - "completion_tokens" or "output"
            - "total_tokens" or "total"
    """
    if not _langfuse_client:
        return

    try:
        kwargs: dict[str, Any] = {"model": model}

        if usage:
            input_tokens = usage.get("prompt_tokens") or usage.get("input") or 0
            output_tokens = usage.get("completion_tokens") or usage.get("output") or 0
            total_tokens = usage.get("total_tokens") or usage.get("total") or (input_tokens + output_tokens)
            kwargs["usage_details"] = {
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens,
            }
            logger.debug(
                "langfuse_usage_reported",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        else:
            logger.debug("langfuse_model_reported", model=model)

        _langfuse_client.update_current_generation(**kwargs)
    except Exception as e:
        logger.warning("langfuse_usage_report_failed", error=str(e))
