from typing import Any

from api.logging_config import get_logger
from api.utils import (
    get_event_for_user,
    get_user_language,
)
from fastapi import HTTPException, status
from services.summary_generator import generate_summary

logger = get_logger()


async def complete_event_session(
    db: Any,
    event_id: str,
    user_id: str,
    transcripts: list[str],
    questions_and_answers: list[dict[str, str]],
) -> dict[str, Any]:
    """Complete an event session: generate summary from plaintext, return result.

    Args:
        transcripts: Decrypted transcripts from client.
        questions_and_answers: Decrypted Q&A from client.

    Returns:
        Dict with id, title, summary, status (plaintext — client encrypts before storage).
    """
    event = await get_event_for_user(db, event_id, user_id)

    if event.get("status") == "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is already completed",
        )

    user_language = await get_user_language(db, user_id)

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

    # Wire evaluation during plaintext phase
    # Note: BackgroundTasks is not available here directly;
    # evaluation will be triggered by the route handler after this returns.

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
