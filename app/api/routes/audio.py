import io
import uuid

from api.deps import CurrentUser, get_current_user
from db.client import get_supabase_client
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/upload")
async def upload_audio(
    file: UploadFile,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Upload audio file to Supabase Storage."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file type",
        )

    supabase = await get_supabase_client()

    audio_bytes = await file.read()
    audio_file = io.BytesIO(audio_bytes)

    file_path = f"{current_user.id}/{event_id}/{uuid.uuid4()}.webm"

    try:
        supabase.storage.from_("audio-recordings").upload(
            file_path,
            audio_file.read(),
            {"content-type": "audio/webm"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}",
        )

    public_url = supabase.storage.from_("audio-recordings").get_public_url(file_path)

    return {
        "audio_url": public_url,
        "file_path": file_path,
    }
