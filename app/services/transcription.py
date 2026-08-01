import io
import time

from api.langfuse_config import report_generation_usage
from api.logging_config import get_logger
from langfuse import observe
from config import get_settings
from openai import AsyncOpenAI
from services.openai_utils import raise_openai_error
from services.storage import StorageService

settings = get_settings()
logger = get_logger()


async def transcribe_audio_url(
    audio_path: str,
    language: str = "pl",
) -> str:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    logger.debug("transcription_path_start", audio_path=audio_path, language=language)

    storage = StorageService()
    audio_content = await storage.download(audio_path)
    logger.debug("transcription_downloaded", size_bytes=len(audio_content))
    return await transcribe_audio_data(audio_content, language)


@observe(as_type="generation")
async def transcribe_audio_data(
    audio_data: bytes,
    language: str = "pl",
) -> str:
    """Transcribe audio bytes using OpenAI Whisper API."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if not audio_data or len(audio_data) == 0:
        raise RuntimeError("Transcription failed: No audio data")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    audio_file = io.BytesIO(audio_data)
    audio_file.name = "recording.webm"

    start_time = time.perf_counter()

    try:
        logger.info(
            "transcription_started",
            language=language,
            audio_size_bytes=len(audio_data),
        )

        result = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="text",
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        if isinstance(result, str):
            transcript = result
        else:
            transcript = str(result)

        transcript_length = len(transcript)

        logger.info(
            "transcription_completed",
            duration_ms=round(duration_ms, 2),
            transcript_length=transcript_length,
        )

        report_generation_usage(model="whisper-1", usage=None)

        return transcript

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        err_msg = str(e)

        logger.error(
            "transcription_failed",
            duration_ms=round(duration_ms, 2),
            error=err_msg,
            error_type=type(e).__name__,
        )

        raise_openai_error(e, "Transcription")
