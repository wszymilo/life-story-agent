import uuid
from typing import Any, Optional

from api.logging_config import get_logger
from api.utils import get_next_sequence_order, get_user_language, require_data
from fastapi import HTTPException, UploadFile, status
from services.storage import StorageService
from services.transcription import transcribe_audio_data

logger = get_logger()

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def add_recording_to_event(
    supabase: Any,
    event_id: str,
    user_id: str,
    file: UploadFile,
    recording_type: str,
    duration_seconds: Optional[float],
    langfuse_trace_id: str | None = None,
) -> dict[str, Any]:
    """Orchestrate adding a recording: validate, upload, transcribe, persist.

    Returns:
        Recording dict (matches AudioRecordingResponse).
    """
    # Validate content type
    if not file.content_type or not file.content_type.startswith("audio/"):
        logger.warning("recording_invalid_content_type", content_type=file.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file type",
        )

    audio_bytes = await file.read()
    audio_size = len(audio_bytes)

    # Validate file size
    if audio_size > MAX_FILE_SIZE_BYTES:
        logger.warning(
            "recording_file_too_large",
            size_mb=round(audio_size / (1024 * 1024), 2),
            max_mb=MAX_FILE_SIZE_MB,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB",
        )

    # Upload to storage
    file_path = f"{user_id}/{event_id}/{uuid.uuid4()}.webm"
    storage = StorageService()

    try:
        public_url = await storage.upload(
            file_path, audio_bytes, content_type="audio/webm"
        )
        logger.info("recording_uploaded", file_path=file_path, size_bytes=audio_size)
    except Exception as e:
        logger.error("recording_upload_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}",
        )

    # Transcribe
    user_language = await get_user_language(supabase, user_id)
    transcript = None
    transcription_error = None
    try:
        audio_data = await storage.download(public_url)
        transcript = await transcribe_audio_data(
            audio_data, language=user_language, langfuse_trace_id=langfuse_trace_id
        )
    except Exception as e:
        transcript = None
        transcription_error = str(e)

    # Persist recording (transcript is encrypted by client; store null initially)
    sequence_order = get_next_sequence_order(supabase, "audio_recordings", event_id)
    recording_data = {
        "event_id": event_id,
        "audio_url": public_url,
        "transcript": None,
        "sequence_order": sequence_order,
        "recording_type": recording_type,
        "duration_seconds": duration_seconds,
    }

    response = supabase.table("audio_recordings").insert(recording_data).execute()
    require_data(response, "Failed to create recording")

    # Mark follow-up question as answered
    if recording_type == "follow_up_response":
        current_question = (
            supabase.table("follow_up_questions")
            .select("id")
            .eq("event_id", event_id)
            .is_("audio_url", "null")
            .eq("was_answered", False)
            .order("sequence_order", desc=False)
            .limit(1)
            .execute()
        )
        if current_question.data:
            supabase.table("follow_up_questions").update(
                {"was_answered": True, "audio_url": public_url}
            ).eq("id", current_question.data[0]["id"]).execute()

    if transcription_error:
        return {
            "id": response.data[0]["id"],
            "event_id": response.data[0]["event_id"],
            "audio_url": response.data[0]["audio_url"],
            "transcript": None,
            "recording_type": response.data[0]["recording_type"],
            "sequence_order": response.data[0]["sequence_order"],
            "duration_seconds": response.data[0].get("duration_seconds"),
            "created_at": response.data[0]["created_at"],
            "detail": "Transcription failed. Your recording is saved.",
        }

    logger.info(
        "add_recording_completed",
        event_id=event_id,
        recording_id=response.data[0]["id"],
        recording_type=recording_type,
    )

    # Return plaintext transcript to client for encryption
    return {
        **response.data[0],
        "transcript": transcript,
    }
