"""Fake objects for testing - replacements for complex external API mocks."""

from .fake_transcription import FakeTranscriptionService
from .fake_llm import FakeLLMService
from .fake_tts import FakeTTSService

__all__ = [
    "FakeTranscriptionService",
    "FakeLLMService",
    "FakeTTSService",
]
