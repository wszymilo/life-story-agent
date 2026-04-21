"""Fake TTS Service - returns predictable audio without real API calls."""

from typing import Any
from dataclasses import dataclass


@dataclass
class TTSResponse:
    """Fake TTS response object."""
    audio: bytes
    duration_seconds: float = 0.0
    language: str = "pl"


class FakeTTSService:
    """A fake TTS service that returns predictable audio."""

    def __init__(self):
        self._calls: list[dict[str, Any]] = []
        self._synthesized_texts: list[str] = []

    def synthesize(
        self, 
        text: str, 
        language: str = "pl",
        voice: str = "default",
    ) -> TTSResponse:
        """Synthesize text to speech.
        
        Returns fake audio with predictable size based on text length.
        """
        self._calls.append({
            "text": text,
            "language": language,
            "voice": voice,
            "text_length": len(text),
        })
        self._synthesized_texts.append(text)

        # Generate fake audio: minimal valid MP3 header + padding
        # Real MP3 is at least ~1152 bytes per frame
        fake_audio = self._generate_silence_mp3(duration_ms=len(text) * 50)

        return TTSResponse(
            audio=fake_audio,
            duration_seconds=len(text) * 0.05,  # Approximate
            language=language,
        )

    def _generate_silence_mp3(self, duration_ms: int) -> bytes:
        """Generate minimal valid MP3-like data."""
        # MP3 frame header (4 bytes) + minimal padding
        header = b'\xff\xfb\x90\x00'
        padding = b'\x00' * max(0, min(duration_ms // 10, 1000))
        return header + padding

    def get_calls(self) -> list[dict[str, Any]]:
        """Get list of calls made to this service."""
        return self._calls

    def get_synthesized_texts(self) -> list[str]:
        """Get list of texts that were synthesized."""
        return self._synthesized_texts.copy()

    def assert_synthesized_with_language(self, expected_lang: str) -> None:
        """Assert that service was called with specific language."""
        langs = [call["language"] for call in self._calls]
        assert expected_lang in langs, \
            f"Expected language {expected_lang}, got {langs}"

    def assert_synthesized_text(self, text: str) -> None:
        """Assert that specific text was synthesized."""
        text_lower = text.lower()
        assert any(text_lower in t.lower() for t in self._synthesized_texts), \
            f"Expected text '{text}', got {self._synthesized_texts}"

    def assert_called(self) -> None:
        """Assert that service was called at least once."""
        assert len(self._calls) > 0, "TTS was not called"

    def reset(self) -> None:
        """Reset call history."""
        self._calls = []
        self._synthesized_texts = []