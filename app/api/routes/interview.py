import uuid

from api.deps import CurrentUser, get_current_user
from api.logging_config import get_logger
from api.rate_limit_config import limiter
from api.schemas.event import AnalyzeRequest, FollowUpRequest, QuestionCreateRequest
from api.utils import (
    get_event_for_user,
    get_next_sequence_order,
    get_user_language,
    require_data,
)
from db.client import get_supabase_client
from fastapi import APIRouter, Depends, HTTPException, Request, status
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

    supabase = await get_supabase_client()

    await get_event_for_user(supabase, event_id_str, user_id_str)

    if not body.transcript.strip():
        logger.warning("analyze_transcript_empty", event_id=event_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is empty",
        )

    # Get user's preferred language
    user_language = await get_user_language(supabase, user_id_str)

    try:
        analysis = await analyze_transcript(body.transcript, language=user_language)
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
        supabase.table("events").update(update_data).eq("id", event_id_str).execute()
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
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate a follow-up question from a plaintext transcript."""
    event_id_str = str(event_id)
    user_id_str = str(current_user.id)

    logger.info("generate_follow_up_endpoint", event_id=event_id_str)

    supabase = await get_supabase_client()

    await get_event_for_user(supabase, event_id_str, user_id_str)

    if not body.transcript.strip():
        logger.warning("generate_follow_up_empty", event_id=event_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is empty",
        )

    # Get user's preferred language
    user_language = await get_user_language(supabase, user_id_str)

    try:
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

    supabase = await get_supabase_client()
    await get_event_for_user(supabase, event_id_str, user_id_str)

    supabase.table("follow_up_questions").delete().eq("event_id", event_id_str).eq("was_answered", False).execute()

    sequence_order = get_next_sequence_order(supabase, "follow_up_questions", event_id_str)

    question_data = {
        "event_id": event_id_str,
        "question_text": body.question_text,
        "sequence_order": sequence_order,
        "was_answered": False,
    }

    result = supabase.table("follow_up_questions").insert(question_data).execute()
    require_data(result, "Failed to create question")

    return {
        "id": result.data[0]["id"],
        "question_text": body.question_text,
        "sequence_order": sequence_order,
        "was_answered": False,
        "created_at": result.data[0]["created_at"],
    }


@router.post("/{event_id}/follow-up/{question_id}/skip")
async def skip_follow_up_question(
    event_id: uuid.UUID,
    question_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Mark a follow-up question as skipped (not answered)."""
    event_id_str = str(event_id)
    question_id_str = str(question_id)

    logger.info("skip_follow_up", event_id=event_id_str, question_id=question_id_str)

    supabase = await get_supabase_client()

    await get_event_for_user(supabase, event_id_str, str(current_user.id))

    question_response = (
        supabase.table("follow_up_questions")
        .select("id")
        .eq("id", question_id_str)
        .eq("event_id", event_id_str)
        .execute()
    )
    require_data(question_response, "Question not found")

    supabase.table("follow_up_questions").update(
        {"was_answered": False}
    ).eq("id", question_id_str).execute()

    logger.info("skip_follow_up_completed", question_id=question_id_str)

    return {"status": "skipped", "question_id": question_id_str}
