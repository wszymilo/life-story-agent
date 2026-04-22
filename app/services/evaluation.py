"""Evaluation service using LLM-as-judge."""

import hashlib
import random

from api.logging_config import get_logger
from api.schemas.evaluation import EvaluationScores
from config import get_settings
from db.client import get_supabase_client
from fastapi import BackgroundTasks
from openai import AsyncOpenAI

settings = get_settings()
logger = get_logger()

MAX_PROMPT_LENGTH = 500


async def evaluate_output(
    prompt_text: str,
    summary_text: str,
    eval_type: str = "summary",
) -> EvaluationScores | None:
    """Evaluate summary quality using LLM as judge.

    Returns structured scores or None if evaluation fails.
    """
    if not settings.openai_api_key:
        logger.warning("eval_skipped_no_api_key")
        return None

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    eval_prompt = f"""Rate this {eval_type} on a scale of 1-5:
- factual_accuracy: Does it accurately reflect the source content?
- coherence: Does it flow logically and naturally?
- completeness: Are key details and themes included?

Source prompt (truncated):
{prompt_text[:MAX_PROMPT_LENGTH]}

{eval_type.capitalize()} to evaluate:
{summary_text[:MAX_PROMPT_LENGTH]}

Provide your ratings as structured output.
"""

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[{"role": "user", "content": eval_prompt}],
            temperature=0.2,
            response_format=EvaluationScores,
        )

        result = response.choices[0].message.parsed
        if result is None:
            logger.warning("eval_parse_failed")
            return None

        logger.info(
            "eval_completed",
            eval_type=eval_type,
            overall_score=result.overall_score,
            factual_accuracy=result.factual_accuracy,
            coherence=result.coherence,
            completeness=result.completeness,
        )

        return result

    except Exception as e:
        from services.openai_utils import raise_openai_error

        try:
            raise_openai_error(e, "Evaluation")
        except RuntimeError as re:
            logger.error("eval_failed", error=str(re))
        return None


def should_evaluate() -> bool:
    """Determine if this output should be evaluated (based on sample rate)."""
    if not settings.eval_enabled:
        return False
    return random.random() < settings.eval_sample_rate


def get_prompt_hash(prompt_text: str) -> str:
    """Generate hash of prompt for deduplication."""
    return hashlib.sha256(prompt_text.encode()).hexdigest()[:16]


def evaluate_in_background(
    background_tasks: BackgroundTasks,
    event_id: str,
    eval_type: str,
    prompt_text: str,
    summary_text: str,
) -> None:
    """Schedule evaluation to run in the background without blocking."""
    background_tasks.add_task(
        _evaluate_and_store, event_id, eval_type, prompt_text, summary_text
    )


async def _evaluate_and_store(
    event_id: str,
    eval_type: str,
    prompt_text: str,
    summary_text: str,
) -> None:
    """Internal: evaluate and store result in database."""
    result = await evaluate_output(prompt_text, summary_text, eval_type)
    if not result:
        return

    supabase = await get_supabase_client()

    try:
        supabase.table("evaluation_results").insert({
            "event_id": event_id,
            "eval_type": eval_type,
            "prompt_hash": get_prompt_hash(prompt_text),
            "prompt_text": prompt_text[:MAX_PROMPT_LENGTH],
            "summary_text": summary_text[:MAX_PROMPT_LENGTH],
            "factual_accuracy": result.factual_accuracy,
            "coherence": result.coherence,
            "completeness": result.completeness,
            "overall_score": result.overall_score,
            "evaluator_model": settings.openai_model,
        }).execute()
        logger.info("eval_stored", event_id=event_id, eval_type=eval_type)
    except Exception as e:
        logger.error("eval_store_failed", error=str(e))
