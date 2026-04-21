import uuid

from api.deps import CurrentUser, get_current_user
from api.utils import (
    get_event_for_user,
    get_next_sequence_order,
    get_transcripts_from_recordings,
    get_user_language,
    require_data,
    validate_recordings_exist,
)
from db.client import get_supabase_client
from fastapi import APIRouter, Depends, HTTPException, status
from services.interview_agent import analyze_transcript, generate_follow_up_question
from utils.date_parser import parse_date


router = APIRouter(prefix="/events", tags=["interview"])


@router.post("/{event_id}/analyze")
async def analyze_event_transcript(
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Analyze an event's transcript to extract time, place, people, and themes."""
    supabase = await get_supabase_client()

    await get_event_for_user(supabase, str(event_id), str(current_user.id))

    recordings_response = (
        supabase.table("audio_recordings")
        .select("transcript")
        .eq("event_id", str(event_id))
        .execute()
    )

    validate_recordings_exist(recordings_response, "No recordings found for this event")
    transcripts = get_transcripts_from_recordings(recordings_response.data)

    if not transcripts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcripts found for this event",
        )

    combined_transcript = "\n\n".join(transcripts)

    # Get user's preferred language
    user_language = await get_user_language(supabase, str(current_user.id))

    try:
        analysis = await analyze_transcript(combined_transcript, language=user_language)
    except Exception as e:
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
        supabase.table("events").update(update_data).eq("id", str(event_id)).execute()

    return {
        "extracted_time": analysis.extracted_time,
        "extracted_place": analysis.extracted_place,
        "people": analysis.people,
        "key_events": analysis.key_events,
        "themes": analysis.themes,
        "summary": analysis.summary,
    }


@router.post("/{event_id}/follow-up")
async def generate_follow_up(
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate a follow-up question for an event."""
    supabase = await get_supabase_client()

    await get_event_for_user(supabase, str(event_id), str(current_user.id))

    recordings_response = (
        supabase.table("audio_recordings")
        .select("transcript")
        .eq("event_id", str(event_id))
        .execute()
    )

    validate_recordings_exist(recordings_response, "No recordings found for this event")
    transcripts = get_transcripts_from_recordings(recordings_response.data)

    if not transcripts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcripts found for this event",
        )

    # Get user's preferred language
    user_language = await get_user_language(supabase, str(current_user.id))

    combined_transcript = "\n\n".join(transcripts)

    existing_questions_response = (
        supabase.table("follow_up_questions")
        .select("question_text")
        .eq("event_id", str(event_id))
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    supabase.table("follow_up_questions").delete().eq("event_id", str(event_id)).eq("was_answered", False).execute()

    sequence_order = get_next_sequence_order(supabase, "follow_up_questions", str(event_id))

    question_data = {
        "event_id": str(event_id),
        "question_text": question.question_text,
        "sequence_order": sequence_order,
        "was_answered": False,
    }

    result = supabase.table("follow_up_questions").insert(question_data).execute()

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
    supabase = await get_supabase_client()

    await get_event_for_user(supabase, str(event_id), str(current_user.id))

    question_response = (
        supabase.table("follow_up_questions")
        .select("id")
        .eq("id", str(question_id))
        .eq("event_id", str(event_id))
        .execute()
    )
    require_data(question_response, "Question not found")

    supabase.table("follow_up_questions").update(
        {"was_answered": False}
    ).eq("id", str(question_id)).execute()

    return {"status": "skipped", "question_id": str(question_id)}
