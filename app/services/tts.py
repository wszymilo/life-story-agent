import time

from api.langfuse_config import log_generation
from api.logging_config import get_logger
from config import get_settings
from openai import AsyncOpenAI

settings = get_settings()
logger = get_logger()


async def generate_speech(
    text: str,
    voice: str = "nova",
    model: str = "gpt-4o-mini-tts",
    response_format: str = "mp3",
) -> tuple[bytes, str]:
    """Generate speech from text using OpenAI TTS API.

    Returns:
        tuple: (audio_bytes, content_type)
    """
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    if voice not in VALID_VOICES:
        raise ValueError(f"Invalid voice. Valid options: {VALID_VOICES}")

    if model not in VALID_TTS_MODELS:
        raise ValueError(f"Invalid model. Valid options: {VALID_TTS_MODELS}")

    if response_format not in VALID_FORMATS:
        raise ValueError(f"Invalid format. Valid options: {VALID_FORMATS}")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    content_type_map = {
        "mp3": "audio/mpeg",
        "opus": "audio/opus",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wav": "audio/wav",
        "pcm": "audio/pcm",
    }

    text_length = len(text)
    start_time = time.perf_counter()

    try:
        logger.info(
            "tts_started",
            voice=voice,
            model=model,
            response_format=response_format,
            text_length=text_length,
        )

        response = await client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        audio_bytes = response.content
        audio_size = len(audio_bytes)

        logger.info(
            "tts_completed",
            duration_ms=round(duration_ms, 2),
            audio_size_bytes=audio_size,
            voice=voice,
        )

        log_generation(
            prompt=text[:500],
            completion="[audio data]",
            model=model,
            metadata={"operation": "tts", "duration_ms": round(duration_ms, 2), "voice": voice},
        )

        return audio_bytes, content_type_map.get(response_format, "audio/mpeg")

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        err_msg = str(e)

        logger.error(
            "tts_failed",
            duration_ms=round(duration_ms, 2),
            error=err_msg,
            error_type=type(e).__name__,
            voice=voice,
        )

        if "api_key" in err_msg.lower():
            raise RuntimeError("TTS failed: Invalid API key")
        if "rate_limit" in err_msg.lower():
            raise RuntimeError("TTS failed: Rate limit exceeded")
        if "max_tokens" in err_msg.lower():
            raise RuntimeError("TTS failed: Text too long (max 4096 characters)")
        raise RuntimeError(f"TTS failed: {err_msg}")


VALID_VOICES = [
    "alloy", "ash", "ballad", "coral", "echo", "fable",
    "onyx", "nova", "sage", "shimmer", "verse", "marin", "cedar"
]

VALID_TTS_MODELS = ["tts-1", "tts-1-hd", "gpt-4o-mini-tts", "gpt-4o-mini-tts-2025-12-15"]

VALID_FORMATS = ["mp3", "opus", "aac", "flac", "wav", "pcm"]