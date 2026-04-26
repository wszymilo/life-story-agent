import uuid

from api.deps import CurrentUser, get_current_user
from api.langfuse_config import story_trace_context
from api.logging_config import get_logger
from api.rate_limit_config import limiter
from api.schemas.event import AnalyzeRequest, FollowUpRequest, QuestionCreateRequest
from api.utils import (
    get_event_for_user,
    get_next_sequence_order,
    get_user_language,
    require_data,
)
from db.query import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from services.interview_agent import analyze_transcript, generate_follow_up_question
from utils.date_parser import parse_date

router = APIRouter(prefix="/events", tags=["interview"])
logger = get_logger()


@router.post("/{event_id}/analyze")
@limiter.limit("5/minute")
async def analyze_event_transcript(
    request: Request,
    event_id: uuid.UUID,
    body: AnalyzeRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Analyze a plaintext transcript to extract time, place, people, and themes."""
    event_id_str = str(event_id)
    user_id_str = str(current_user.id)

    logger.info("analyze_transcript_endpoint", event_id=event_id_str)

    db = await get_db()

    await get_event_for_user(db, event_id_str, user_id_str)

    if not body.transcript.strip():
        logger.warning("analyze_transcript_empty", event_id=event_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is empty",
        )

    user_language = await get_user_language(db, user_id_str)

    event_response = (
        db.table("events")
        .select("trace_id")
        .eq("id", event_id_str)
        .execute()
    )
    trace_id = None
    if event_response.data:
        trace_id = event_response.data[0].get("trace_id")

    try:
        with story_trace_context(trace_id, user_id_str):
            analysis = await analyze_transcript(
                body.transcript,
                language=user_language,
            )
    except Exception as e:
        logger.error("analyze_transcript_failed", event_id=event_id_str, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    update_data = {}
    if analysis.extracted_time:
        parsed_date = parse_date(analysis.extracted_time)
        if parsed_date:
            update_data["time_anchor_date"] = parsed_date.isoformat()
            update_data["time_anchor"] = analysis.extracted_time

    if analysis.extracted_place:
        update_data["place"] = analysis.extracted_place

    if update_data:
        db.table("events").update(update_data).eq("id", event_id_str).execute()
        logger.info("analyze_transcript_updated_event", event_id=event_id_str, updates=list(update_data.keys()))

    result = {
        "extracted_time": analysis.extracted_time,
        "extracted_place": analysis.extracted_place,
        "people": analysis.people,
        "key_events": analysis.key_events,
        "themes": analysis.themes,
        "summary": analysis.summary,
    }

    logger.info("analyze_transcript_completed", event_id=event_id_str, has_time=analysis.extracted_time is not None, has_place=analysis.extracted_place is not None)

    return result


@router.post("/{event_id}/follow-up")
@limiter.limit("5/minute")
async def generate_follow_up(
    request: Request,
    event_id: uuid.UUID,
    body: FollowUpRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate a follow-up question from a plaintext transcript."""
    event_id_str = str(event_id)
    user_id_str = str(current_user.id)

    logger.info("generate_follow_up_endpoint", event_id=event_id_str)

    db = await get_db()

    await get_event_for_user(db, event_id_str, user_id_str)

    if not body.transcript.strip():
        logger.warning("generate_follow_up_empty", event_id=event_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is empty",
        )

    user_language = await get_user_language(db, user_id_str)

    event_response = (
        db.table("events")
        .select("trace_id")
        .eq("id", event_id_str)
        .execute()
    )
    trace_id = None
    if event_response.data:
        trace_id = event_response.data[0].get("trace_id")

    try:
        with story_trace_context(trace_id, user_id_str):
            question = await generate_follow_up_question(
                transcript=body.transcript,
                existing_questions=body.existing_questions,
                language=user_language,
            )
    except Exception as e:
        logger.error("generate_follow_up_failed", event_id=event_id_str, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    from services.evaluation import evaluate_question_in_background, should_evaluate
    if should_evaluate():
        evaluate_question_in_background(
            background_tasks,
            event_id=event_id_str,
            transcript=body.transcript,
            question_text=question.question_text,
            existing_questions=body.existing_questions,
            trace_id=trace_id,
        )

    return {
        "question_text": question.question_text,
        "question_type": question.question_type,
    }


@router.post("/{event_id}/questions", status_code=status.HTTP_201_CREATED)
async def create_question(
    request: Request,
    event_id: uuid.UUID,
    body: QuestionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Store an encrypted follow-up question."""
    event_id_str = str(event_id)
    user_id_str = str(current_user.id)

    db = await get_db()
    await get_event_for_user(db, event_id_str, user_id_str)

    db.table("follow_up_questions").delete().eq("event_id", event_id_str).eq("was_answered", False).execute()

    sequence_order = await get_next_sequence_order(db, "follow_up_questions", event_id_str)

    question_data = {
        "event_id": event_id_str,
        "question_text": body.question_text,
        "sequence_order": sequence_order,
        "was_answered": False,
    }

    result = db.table("follow_up_questions").insert(question_data).execute()
    require_data(result, "Failed to create question")

    return {
        "id": result.data[0]["id"],
        "question_text": body.question_text,
        "sequence_order": sequence_order,
        "was_answered": False,
        "created_at": result.data[0]["created_at"],
    }
