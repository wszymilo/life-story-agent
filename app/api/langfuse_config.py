"""LangFuse LLM tracing configuration with trace context, token usage, cost tracking, and scoring."""

from contextvars import ContextVar
from typing import Any

from langfuse import Langfuse

from api.logging_config import get_logger
from config import get_settings

settings = get_settings()
logger = get_logger()

_langfuse_client: Langfuse | None = None

# Cost constants (USD per 1M tokens, or per unit)
_COST_PER_1M_TOKENS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
}
_COST_PER_MINUTE = {
    "whisper-1": 0.006,
}
_COST_PER_1K_CHARS = {
    "gpt-4o-mini-tts": 0.015,
    "gpt-4o-mini-tts-2025-12-15": 0.015,
    "tts-1": 0.015,
    "tts-1-hd": 0.030,
}

# ContextVars for automatic trace/span propagation without explicit passing
trace_ctx: ContextVar[str | None] = ContextVar("trace_ctx", default=None)
span_ctx: ContextVar[str | None] = ContextVar("span_ctx", default=None)


def _compute_cost(model: str, usage: dict[str, Any] | None) -> float | None:
    """Compute cost in USD from usage metadata."""
    if not usage:
        return None

    cost = 0.0
    # Chat completion cost
    if model in _COST_PER_1M_TOKENS:
        rates = _COST_PER_1M_TOKENS[model]
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost += (prompt_tokens / 1_000_000) * rates["input"]
        cost += (completion_tokens / 1_000_000) * rates["output"]
        return round(cost, 6)

    # Whisper cost (per minute)
    if model in _COST_PER_MINUTE:
        minutes = usage.get("duration_minutes", 0)
        cost = minutes * _COST_PER_MINUTE[model]
        return round(cost, 6)

    # TTS cost (per 1K characters)
    if model in _COST_PER_1K_CHARS:
        chars = usage.get("characters", 0)
        cost = (chars / 1_000) * _COST_PER_1K_CHARS[model]
        return round(cost, 6)

    return None


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
    """Create a new LangFuse trace and set it as current context.

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
        trace_ctx.set(trace_id)
        span_ctx.set(None)
        logger.debug("langfuse_trace_started", trace_id=trace_id, name=name)
        return trace_id
    except Exception as e:
        logger.warning("langfuse_trace_failed", error=str(e))
        return None


def start_span(name: str, metadata: dict | None = None) -> str | None:
    """Start a new span under the current trace.

    Returns the span_id or None if LangFuse is not configured.
    """
    if not _langfuse_client:
        return None

    current_trace = trace_ctx.get()
    if not current_trace:
        return None

    try:
        span = _langfuse_client.span(
            trace_id=current_trace,
            name=name,
            metadata=metadata or {},
        )
        span_id = str(span.id)
        span_ctx.set(span_id)
        logger.debug("langfuse_span_started", trace_id=current_trace, span_id=span_id, name=name)
        return span_id
    except Exception as e:
        logger.warning("langfuse_span_failed", error=str(e))
        return None


def log_generation(
    prompt: str,
    completion: str,
    model: str,
    usage: dict[str, Any] | None = None,
    metadata: dict | None = None,
    status: str = "success",
    user_id: str | None = None,
) -> None:
    """Log an LLM generation to LangFuse inside the current trace/span context.

    Automatically computes cost from usage if provided.
    """
    if not _langfuse_client:
        return

    current_trace = trace_ctx.get()
    if not current_trace:
        return

    try:
        cost = _compute_cost(model, usage)
        meta = {
            "user_id": user_id,
            "status": status,
            **(metadata or {}),
        }
        if cost is not None:
            meta["cost_usd"] = cost

        _langfuse_client.generation(
            trace_id=current_trace,
            name="llm_generation",
            input={"prompt": prompt[:1000]},
            output={"completion": completion[:1000]},
            model=model,
            usage=usage,
            metadata=meta,
        )
        logger.debug("langfuse_generation_logged", trace_id=current_trace, model=model, status=status)
    except Exception as e:
        logger.warning("langfuse_log_failed", error=str(e))


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


def set_trace_context(trace_id: str | None) -> None:
    """Set the current trace context (for crossing async boundaries)."""
    trace_ctx.set(trace_id)
    span_ctx.set(None)


def get_trace_context() -> str | None:
    """Get the current trace context."""
    return trace_ctx.get()


def get_span_context() -> str | None:
    """Get the current span context."""
    return span_ctx.get()
