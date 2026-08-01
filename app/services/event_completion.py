from typing import Any

from api.logging_config import get_logger
from db.repositories import EventRepository, UserRepository
from fastapi import HTTPException, status
from services.summary_generator import generate_summary

logger = get_logger()


async def complete_event_session(
    event_repo: EventRepository,
    user_repo: UserRepository,
    event_id: str,
    user_id: str,
    transcripts: list[str],
    questions_and_answers: list[dict[str, str]],
) -> dict[str, Any]:
    event = await event_repo.fetch_by_id(event_id, user_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.get("status") == "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is already completed",
        )

    user_language = await user_repo.fetch_language(user_id)

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

    return {
        "id": event_id,
        "title": summary_result.title,
        "summary": summary_result.summary,
        "status": "complete",
        "time_anchor_date": summary_result.time_anchor_date.isoformat() if summary_result.time_anchor_date else None,
        "_eval_payload": {
            "transcripts": transcripts,
            "summary": summary_result.summary,
        },
    }
