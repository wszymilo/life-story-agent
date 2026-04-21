import uuid

from api.deps import CurrentUser, get_current_user
from api.logging_config import get_logger
from api.rate_limit_config import limiter
from api.utils import (
    get_event_for_user,
    get_next_sequence_order,
    get_transcripts_from_recordings,
    get_user_language,
    require_data,
    validate_recordings_exist,
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
    current_user: CurrentUser = Depends(get_current_user),
):
    """Analyze an event's transcript to extract time, place, people, and themes."""
    event_id_str = str(event_id)
    user_id_str = str(current_user.id)

    logger.info("analyze_transcript_endpoint", event_id=event_id_str)

    supabase = await get_supabase_client()

    await get_event_for_user(supabase, event_id_str, user_id_str)

    recordings_response = (
        supabase.table("audio_recordings")
        .select("transcript")
        .eq("event_id", event_id_str)
        .execute()
    )

    validate_recordings_exist(recordings_response, "No recordings found for this event")
    transcripts = get_transcripts_from_recordings(recordings_response.data)

    if not transcripts:
        logger.warning("analyze_transcript_no_transcripts", event_id=event_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcripts found for this event",
        )

    combined_transcript = "\n\n".join(transcripts)

    # Get user's preferred language
    user_language = await get_user_language(supabase, user_id_str)

    try:
        analysis = await analyze_transcript(combined_transcript, language=user_language)
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
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate a follow-up question for an event."""
    event_id_str = str(event_id)
    user_id_str = str(current_user.id)

    logger.info("generate_follow_up_endpoint", event_id=event_id_str)

    supabase = await get_supabase_client()

    await get_event_for_user(supabase, event_id_str, user_id_str)

    recordings_response = (
        supabase.table("audio_recordings")
        .select("transcript")
        .eq("event_id", event_id_str)
        .execute()
    )

    validate_recordings_exist(recordings_response, "No recordings found for this event")
    transcripts = get_transcripts_from_recordings(recordings_response.data)

    if not transcripts:
        logger.warning("generate_follow_up_no_transcripts", event_id=event_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcripts found for this event",
        )

    # Get user's preferred language
    user_language = await get_user_language(supabase, user_id_str)

    combined_transcript = "\n\n".join(transcripts)

    existing_questions_response = (
        supabase.table("follow_up_questions")
        .select("question_text")
        .eq("event_id", event_id_str)
        .execute()
    )

    existing_questions = [
        q.get("question_text")
        for q in existing_questions_response.data
        if q.get("question_text")
    ]

    try:
        question = await generate_follow_up_question(
            transcript=combined_transcript,
            existing_questions=existing_questions,
            language=user_language,
        )
    except Exception as e:
        logger.error("generate_follow_up_failed", event_id=event_id_str, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    supabase.table("follow_up_questions").delete().eq("event_id", event_id_str).eq("was_answered", False).execute()

    sequence_order = get_next_sequence_order(supabase, "follow_up_questions", event_id_str)

    question_data = {
        "event_id": event_id_str,
        "question_text": question.question_text,
        "sequence_order": sequence_order,
        "was_answered": False,
    }

    result = supabase.table("follow_up_questions").insert(question_data).execute()

    logger.info(
        "generate_follow_up_completed",
        event_id=event_id_str,
        question_id=result.data[0]["id"],
        question_type=question.question_type,
    )

    return {
        "id": result.data[0]["id"],
        "question_text": question.question_text,
        "question_type": question.question_type,
        "context": question.context,
        "target_area": question.target_area,
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
