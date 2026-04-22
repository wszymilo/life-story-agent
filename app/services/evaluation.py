"""Evaluation service using LLM-as-judge."""

import asyncio
import hashlib
import random

from api.logging_config import get_logger
from config import get_settings

settings = get_settings()
logger = get_logger()


async def evaluate_output(
    prompt_text: str,
    summary_text: str,
    eval_type: str = "summary",
) -> dict | None:
    """Evaluate summary quality using GPT-4 as judge.
    
    Returns dict with factual_accuracy, coherence, completeness, overall_score (1-5).
    """
    if not settings.openai_api_key:
        logger.warning("eval_skipped_no_api_key")
        return None

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    eval_prompt = f"""Rate this {eval_type} on a scale of 1-5:
- factual_accuracy: Does it accurately reflect the source content?
- coherence: Does it flow logically and naturally?
- completeness: Are key details and themes included?

Source prompt (truncated):
{prompt_text[:500]}

{eval_type.capitalize()} to evaluate:
{summary_text[:500]}

Respond with ONLY a JSON object:
{{"factual_accuracy": 1-5, "coherence": 1-5, "completeness": 1-5, "overall_score": 1-5, "explanation": "brief text"}}
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": eval_prompt}],
            temperature=0.2,
        )

        content = response.choices[0].message.content or ""
        
        # Parse JSON from response
        import json
        result = {}
        try:
            # Extract JSON from potential markdown code block
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            result = json.loads(content.strip())
        except json.JSONDecodeError:
            logger.warning("eval_parse_failed", content=content[:200])
            return None

        logger.info(
            "eval_completed",
            eval_type=eval_type,
            overall_score=result.get("overall_score"),
            factual_accuracy=result.get("factual_accuracy"),
            coherence=result.get("coherence"),
            completeness=result.get("completeness"),
        )

        return result

    except Exception as e:
        logger.error("eval_failed", error=str(e))
        return None


def should_evaluate() -> bool:
    """Determine if this output should be evaluated (based on sample rate)."""
    if not settings.eval_enabled:
        return False
    return random.random() < settings.eval_sample_rate


def get_prompt_hash(prompt_text: str) -> str:
    """Generate hash of prompt for deduplication."""
    return hashlib.sha256(prompt_text.encode()).hexdigest()[:16]


async def evaluate_in_background(
    event_id: str,
    eval_type: str,
    prompt_text: str,
    summary_text: str,
) -> None:
    """Run evaluation in background without blocking."""
    asyncio.create_task(
        _evaluate_and_store(event_id, eval_type, prompt_text, summary_text)
    )


async def _evaluate_and_store(
    event_id: str,
    eval_type: str,
    prompt_text: str,
    summary_text: str,
) -> None:
    """Internal: evaluate and store result in database."""
    from db.client import get_supabase_client

    result = await evaluate_output(prompt_text, summary_text, eval_type)
    if not result:
        return

    supabase = await get_supabase_client()

    try:
        supabase.table("evaluation_results").insert({
            "event_id": event_id,
            "eval_type": eval_type,
            "prompt_hash": get_prompt_hash(prompt_text),
            "prompt_text": prompt_text[:500],
            "summary_text": summary_text[:500],
            "factual_accuracy": result.get("factual_accuracy"),
            "coherence": result.get("coherence"),
            "completeness": result.get("completeness"),
            "overall_score": result.get("overall_score"),
            "evaluator_model": "gpt-4o",
        })
        logger.info("eval_stored", event_id=event_id, eval_type=eval_type)
    except Exception as e:
        logger.error("eval_store_failed", error=str(e))
