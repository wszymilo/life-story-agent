from typing import Any

from api.logging_config import get_logger
from api.utils import (
    get_event_for_user,
    get_transcripts_from_recordings,
    get_user_language,
    require_data,
    serialize_update_data,
)
from fastapi import HTTPException, status
from services.summary_generator import generate_summary

logger = get_logger()


async def complete_event_session(
    supabase: Any,
    event_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Complete an event session: gather artifacts, generate summary, update event.

    Returns:
        Dict with id, title, summary, status.
    """
    # Verify ownership
    event = await get_event_for_user(supabase, event_id, user_id)

    # Check if already completed
    if event.get("status") == "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is already completed",
        )

    # Get all transcripts
    recordings_response = (
        supabase.table("audio_recordings")
        .select("transcript", "recording_type")
        .eq("event_id", event_id)
        .execute()
    )
    transcripts = get_transcripts_from_recordings(
        recordings_response.data if recordings_response.data else []
    )

    # Get Q&A from follow-up questions
    questions_response = (
        supabase.table("follow_up_questions")
        .select("question_text", "was_answered", "audio_url")
        .eq("event_id", event_id)
        .execute()
    )

    questions_and_answers = []
    if questions_response.data:
        for q in questions_response.data:
            if q.get("was_answered") and q.get("audio_url"):
                answer_recording = (
                    supabase.table("audio_recordings")
                    .select("transcript")
                    .eq("audio_url", q["audio_url"])
                    .limit(1)
                    .execute()
                )
                answer_text = None
                if answer_recording.data and answer_recording.data[0].get("transcript"):
                    answer_text = answer_recording.data[0]["transcript"]

                questions_and_answers.append({
                    "question": q.get("question_text", ""),
                    "answer": answer_text or "",
                })

    # Generate summary
    user_language = await get_user_language(supabase, user_id)

    try:
        summary_result = await generate_summary(
            transcripts=transcripts,
            questions_and_answers=questions_and_answers,
            language=user_language,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}",
        )

    # Update event
    update_data = {
        "summary": summary_result.summary,
        "title": summary_result.title,
        "status": "complete",
    }
    if summary_result.time_anchor_date:
        update_data["time_anchor_date"] = summary_result.time_anchor_date.isoformat()
    serialize_update_data(update_data)

    updated_event = (
        supabase.table("events")
        .update(update_data)
        .eq("id", event_id)
        .execute()
    )
    require_data(updated_event, "Failed to update event")

    return {
        "id": event_id,
        "title": summary_result.title,
        "summary": summary_result.summary,
        "status": "complete",
    }
