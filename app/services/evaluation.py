import random

from api.langfuse_config import log_score
from api.logging_config import get_logger
from api.schemas.evaluation import EvaluationScores, QuestionEvaluationScores
from config import get_settings
from db.client import get_pool
from db.repositories import EvaluationRepository
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


async def evaluate_question(
    transcript: str,
    question_text: str,
    existing_questions: list[str],
) -> QuestionEvaluationScores | None:
    if not settings.openai_api_key:
        logger.warning("question_eval_skipped_no_api_key")
        return None

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    eval_prompt = f"""Rate this follow-up question on a scale of 1-5:
- relevance: Does the question relate to the transcript content?
- specificity: Is it concrete and specific rather than generic?
- open_endedness: Does it invite elaboration (not yes/no)?
- diversity: Does it explore a different theme from previous questions?
- expected_richness: Would the answer likely reveal new information?

Transcript (truncated):
{transcript[:MAX_PROMPT_LENGTH]}

Question to evaluate:
{question_text[:MAX_PROMPT_LENGTH]}

Previous questions (avoiding duplication):
{chr(10).join(f"- {q}" for q in existing_questions[:5]) or "None"}

Provide your ratings as structured output.
"""

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[{"role": "user", "content": eval_prompt}],
            temperature=0.2,
            response_format=QuestionEvaluationScores,
        )

        result = response.choices[0].message.parsed
        if result is None:
            logger.warning("question_eval_parse_failed")
            return None

        logger.info(
            "question_eval_completed",
            overall_score=result.overall_score,
            relevance=result.relevance,
            specificity=result.specificity,
        )

        return result

    except Exception as e:
        from services.openai_utils import raise_openai_error

        try:
            raise_openai_error(e, "Question Evaluation")
        except RuntimeError as re:
            logger.error("question_eval_failed", error=str(re))
        return None


def should_evaluate() -> bool:
    if not settings.eval_enabled:
        return False
    return random.random() < settings.eval_sample_rate


def evaluate_in_background(
    background_tasks: BackgroundTasks,
    event_id: str,
    eval_type: str,
    prompt_text: str,
    summary_text: str,
    trace_id: str | None = None,
) -> None:
    background_tasks.add_task(
        _evaluate_and_store, event_id, eval_type, prompt_text, summary_text, trace_id
    )


def evaluate_question_in_background(
    background_tasks: BackgroundTasks,
    event_id: str,
    transcript: str,
    question_text: str,
    existing_questions: list[str],
    trace_id: str | None = None,
) -> None:
    background_tasks.add_task(
        _evaluate_question_and_store, event_id, transcript, question_text, existing_questions, trace_id
    )


async def _evaluate_and_store(
    event_id: str,
    eval_type: str,
    prompt_text: str,
    summary_text: str,
    trace_id: str | None = None,
) -> None:
    result = await evaluate_output(prompt_text, summary_text, eval_type)
    if not result:
        return
    await _store_scores(event_id, eval_type, result, trace_id)


async def _evaluate_question_and_store(
    event_id: str,
    transcript: str,
    question_text: str,
    existing_questions: list[str],
    trace_id: str | None = None,
) -> None:
    result = await evaluate_question(transcript, question_text, existing_questions)
    if not result:
        return
    await _store_question_scores(event_id, result, trace_id)


async def _store_scores(
    event_id: str,
    eval_type: str,
    result: EvaluationScores,
    trace_id: str | None = None,
) -> None:
    try:
        pool = await get_pool()
        repo = EvaluationRepository(pool)
        await repo.insert({
            "event_id": event_id,
            "eval_type": eval_type,
            "factual_accuracy": result.factual_accuracy,
            "coherence": result.coherence,
            "completeness": result.completeness,
            "overall_score": result.overall_score,
            "evaluator_model": settings.openai_model,
        })
        logger.info("eval_stored", event_id=event_id, eval_type=eval_type)
    except Exception as e:
        logger.error("eval_store_failed", error=str(e))

    if trace_id:
        log_score(trace_id, "factual_accuracy", result.factual_accuracy or 0, f"eval_type={eval_type}")
        log_score(trace_id, "coherence", result.coherence or 0, f"eval_type={eval_type}")
        log_score(trace_id, "completeness", result.completeness or 0, f"eval_type={eval_type}")
        log_score(trace_id, "overall_score", result.overall_score or 0, f"eval_type={eval_type}")


async def _store_question_scores(
    event_id: str,
    result: QuestionEvaluationScores,
    trace_id: str | None = None,
) -> None:
    try:
        pool = await get_pool()
        repo = EvaluationRepository(pool)
        await repo.insert({
            "event_id": event_id,
            "eval_type": "question",
            "factual_accuracy": result.relevance,
            "coherence": result.specificity,
            "completeness": result.open_endedness,
            "overall_score": result.overall_score,
            "evaluator_model": settings.openai_model,
        })
        logger.info("question_eval_stored", event_id=event_id)
    except Exception as e:
        logger.error("question_eval_store_failed", error=str(e))

    if trace_id:
        log_score(trace_id, "question_relevance", result.relevance or 0)
        log_score(trace_id, "question_specificity", result.specificity or 0)
        log_score(trace_id, "question_open_endedness", result.open_endedness or 0)
        log_score(trace_id, "question_diversity", result.diversity or 0)
        log_score(trace_id, "question_expected_richness", result.expected_richness or 0)
        log_score(trace_id, "question_overall_score", result.overall_score or 0)


async def store_evaluation_scores(
    event_id: str,
    eval_type: str,
    scores: EvaluationScores,
) -> None:
    await _store_scores(event_id, eval_type, scores)
