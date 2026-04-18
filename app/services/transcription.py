import io

from config import get_settings

settings = get_settings()


async def transcribe_audio_url(audio_url: str, language: str = "pl") -> str:
    """Transcribe audio from URL using OpenAI Whisper API."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    # Check if this is a Supabase Storage URL (private bucket scenario)
    # URL format: https://...supabase.co/storage/v1/object/public/audio-recordings/...
    if "/storage/v1/object/" in audio_url and "audio-recordings" in audio_url:
        # Extract file path from URL (everything after /audio-recordings/)
        path_parts = audio_url.split("/audio-recordings/")
        if len(path_parts) > 1:
            file_path = path_parts[1]

            # Use service key to download from private bucket
            from supabase import create_client

            service_client = create_client(settings.supabase_url, settings.supabase_service_key)
            audio_content = service_client.storage.from_("audio-recordings").download(file_path)

            # Transcribe the downloaded content
            return await transcribe_audio_data(audio_content, language)

    # Fallback: try direct HTTP download for non-Supabase URLs
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(audio_url)
        response.raise_for_status()
        audio_content = response.content

    return await transcribe_audio_data(audio_content, language)


async def transcribe_audio_data(audio_data: bytes, language: str = "pl") -> str:
    """Transcribe audio bytes using OpenAI Whisper API."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if not audio_data or len(audio_data) == 0:
        raise RuntimeError("Transcription failed: No audio data")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    audio_file = io.BytesIO(audio_data)
    audio_file.name = "recording.webm"

    try:
        result = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="text",
        )
        # Whisper returns string when response_format="text"
        if isinstance(result, str):
            return result
        return str(result)
    except Exception as e:
        err_msg = str(e)
        # Simplify common errors
        if "Incorrect API key" in err_msg or "invalid_api_key" in err_msg:
            raise RuntimeError("Transcription failed: Invalid API key")
        if "api_key" in err_msg.lower():
            raise RuntimeError("Transcription failed: API key issue")
        raise RuntimeError("Transcription failed")
