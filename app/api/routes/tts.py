from api.deps import CurrentUser, get_current_user
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.tts import generate_speech

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    voice: str = "nova"
    model: str = "gpt-4o-mini-tts"
    response_format: str = "mp3"


@router.post("/generate")
async def generate_tts(
    request: TTSRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate speech from text and return audio as streaming response."""
    try:
        audio_bytes, content_type = await generate_speech(
            text=request.text,
            voice=request.voice,
            model=request.model,
            response_format=request.response_format,
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
