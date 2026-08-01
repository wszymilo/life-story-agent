import uuid
from typing import Any, Optional

from api.logging_config import get_logger
from db.repositories import RecordingRepository, UserRepository
from fastapi import HTTPException, UploadFile, status
from services.storage import StorageService
from services.transcription import transcribe_audio_data

logger = get_logger()

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def add_recording_to_event(
    recording_repo: RecordingRepository,
    user_repo: UserRepository,
    event_id: str,
    user_id: str,
    file: UploadFile,
    recording_type: str,
    duration_seconds: Optional[float],
) -> dict[str, Any]:
    if not file.content_type or not file.content_type.startswith("audio/"):
        logger.warning("recording_invalid_content_type", content_type=file.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file type",
        )

    audio_bytes = await file.read()
    audio_size = len(audio_bytes)

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

    file_path = f"{user_id}/{event_id}/{uuid.uuid4()}.webm"
    storage = StorageService()

    try:
        audio_path = await storage.upload(
            file_path, audio_bytes, content_type="audio/webm"
        )
        logger.info("recording_uploaded", file_path=file_path, size_bytes=audio_size)
    except Exception as e:
        logger.error("recording_upload_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}",
        )

    user_language = await user_repo.fetch_language(user_id)
    transcript = None
    transcription_error = None
    try:
        audio_data = await storage.download(audio_path)
        transcript = await transcribe_audio_data(audio_data, language=user_language)
    except Exception as e:
        transcript = None
        transcription_error = str(e)

    sequence_order = await recording_repo.next_sequence_order("audio_recordings", event_id)
    recording_data = {
        "event_id": event_id,
        "audio_url": audio_path,
        "transcript": None,
        "sequence_order": sequence_order,
        "recording_type": recording_type,
        "duration_seconds": duration_seconds,
    }

    recording = await recording_repo.insert(recording_data)

    if recording_type == "follow_up_response":
        question = await recording_repo.fetch_unanswered_question(event_id)
        if question:
            await recording_repo.mark_answered(question["id"], audio_path)

    if transcription_error:
        return {
            **recording,
            "transcript": None,
            "detail": "Transcription failed. Your recording is saved.",
        }

    logger.info(
        "add_recording_completed",
        event_id=event_id,
        recording_id=recording["id"],
        recording_type=recording_type,
    )

    return {
        **recording,
        "transcript": transcript,
    }
