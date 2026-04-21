"""Fake Transcription Service - returns predictable transcripts without real API calls."""

from typing import Any


class FakeTranscriptionService:
    """A fake transcription service that returns predefined transcripts."""

    def __init__(self, transcripts: dict[bytes, str] | None = None):
        """Initialize with optional preset transcripts.
        
        Args:
            transcripts: Dict mapping audio data to transcript text. 
                       If not provided, uses default test transcript.
        """
        self._transcripts = transcripts or {}
        self._default_transcript = "To był piękny słoneczny dzień w Warszawie. Pamiętam jak przez całe popołudnie bawiłem się z dziećmi na podwórku."
        self._calls: list[dict[str, Any]] = []

    def set_transcript(self, audio_data: bytes, transcript: str) -> None:
        """Set a transcript for specific audio data."""
        self._transcripts[audio_data] = transcript

    def transcribe(self, audio_data: bytes, language: str = "pl") -> str:
        """Transcribe audio data.
        
        Returns predefined transcript or default test transcript.
        """
        self._calls.append({
            "audio_data": audio_data,
            "language": language,
            "length": len(audio_data) if audio_data else 0,
        })
        
        # Return matching transcript or default
        if audio_data in self._transcripts:
            return self._transcripts[audio_data]
        
        # Return language-specific default for testing
        return self._default_transcript

    def get_calls(self) -> list[dict[str, Any]]:
        """Get list of calls made to this service."""
        return self._calls

    def assert_called_with_language(self, expected_lang: str) -> None:
        """Assert that service was called with specific language."""
        langs = [call["language"] for call in self._calls]
        assert expected_lang in langs, f"Expected language {expected_lang}, got {langs}"

    def assert_called(self) -> None:
        """Assert that service was called at least once."""
        assert len(self._calls) > 0, "Service was not called"

    def reset(self) -> None:
        """Reset call history."""
        self._calls = []