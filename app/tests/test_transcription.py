"""Tests for transcription service using FakeTranscriptionService."""

import pytest

from tests.fakes.fake_transcription import FakeTranscriptionService


class TestTranscriptionWithFake:
    """Tests using FakeTranscriptionService to avoid real API calls."""

    @pytest.fixture
    def fake_transcription(self):
        """Create a fake transcription service."""
        return FakeTranscriptionService()

    def test_fake_returns_default_transcript(self, fake_transcription):
        """Test that fake returns default transcript."""
        fake_audio = b"fake audio data"
        result = fake_transcription.transcribe(fake_audio, language="pl")
        
        assert "Warszawie" in result
        assert "podwórku" in result

    def test_fake_tracks_calls(self, fake_transcription):
        """Test that fake tracks method calls."""
        fake_audio = b"test audio"
        fake_transcription.transcribe(fake_audio, language="en")
        
        calls = fake_transcription.get_calls()
        assert len(calls) == 1
        assert calls[0]["language"] == "en"

    def test_fake_with_custom_transcript(self, fake_transcription):
        """Test that fake returns custom transcript when set."""
        custom_audio = b"custom audio"
        custom_transcript = "Custom test transcript about childhood"
        fake_transcription.set_transcript(custom_audio, custom_transcript)
        
        result = fake_transcription.transcribe(custom_audio)
        assert result == custom_transcript

    def test_fake_assert_language(self, fake_transcription):
        """Test language assertion helper."""
        fake_transcription.transcribe(b"audio1", language="pl")
        fake_transcription.transcribe(b"audio2", language="en")
        
        fake_transcription.assert_called_with_language("pl")
        fake_transcription.assert_called_with_language("en")

    def test_fake_reset(self, fake_transcription):
        """Test that reset clears call history."""
        fake_transcription.transcribe(b"audio1")
        fake_transcription.transcribe(b"audio2")
        
        fake_transcription.reset()
        
        assert len(fake_transcription.get_calls()) == 0


class TestFakeIndependently:
    """Verify fake works independently of real API."""

    def test_fake_can_be_used_without_real_api(self):
        """Verify fake works independently of real API."""
        fake = FakeTranscriptionService()
        
        audio_short = b"short"
        audio_medium = b"medium length audio data"
        
        result1 = fake.transcribe(audio_short, "pl")
        result2 = fake.transcribe(audio_medium, "en")
        
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        
        assert "Warszawie" in result1
        assert "Warszawie" in result2
