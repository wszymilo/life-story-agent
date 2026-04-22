from api.deps import CurrentUser, get_current_user
from api.rate_limit_config import limiter
from config import get_settings
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.tts import generate_speech

settings = get_settings()

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    voice: str = "nova"
    model: str = settings.tts_model
    response_format: str = "mp3"


@router.post("/generate")
@limiter.limit("20/minute")
async def generate_tts(
    request: Request,
    tts_request: TTSRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate speech from text and return audio as streaming response."""
    try:
        audio_bytes, content_type = await generate_speech(
            text=tts_request.text,
            voice=tts_request.voice,
            model=tts_request.model,
            response_format=tts_request.response_format,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return StreamingResponse(
        iter([audio_bytes]),
        media_type=content_type,
        headers={
            "Content-Disposition": "inline",
        },
    )
