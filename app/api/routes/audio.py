import io
import uuid

from api.deps import CurrentUser, get_current_user
from api.logging_config import get_logger
from api.rate_limit_config import limiter
from db.client import get_supabase_client
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status

router = APIRouter(prefix="/audio", tags=["audio"])
logger = get_logger()

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_audio(
    request: Request,
    file: UploadFile,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Upload audio file to Supabase Storage."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        logger.warning("upload_invalid_content_type", content_type=file.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file type",
        )

    supabase = await get_supabase_client()

    audio_bytes = await file.read()
    audio_size = len(audio_bytes)

    if audio_size > MAX_FILE_SIZE_BYTES:
        logger.warning(
            "upload_file_too_large",
            size_mb=round(audio_size / (1024 * 1024), 2),
            max_mb=MAX_FILE_SIZE_MB,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB",
        )

    audio_file = io.BytesIO(audio_bytes)

    file_path = f"{current_user.id}/{event_id}/{uuid.uuid4()}.webm"

    try:
        supabase.storage.from_("audio-recordings").upload(
            file_path,
            audio_file.read(),
            {"content-type": "audio/webm"},
        )
        logger.info("upload_success", file_path=file_path, size_bytes=audio_size)
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}",
        )

    public_url = supabase.storage.from_("audio-recordings").get_public_url(file_path)

    return {
        "audio_url": public_url,
        "file_path": file_path,
    }
