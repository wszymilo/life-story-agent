"""Tests for TTS service using FakeTTSService."""

import pytest

from tests.fakes.fake_tts import FakeTTSService


class TestFakeTTSService:
    """Tests for FakeTTSService."""

    @pytest.fixture
    def fake_tts(self):
        """Create a fake TTS service."""
        return FakeTTSService()

    def test_fake_returns_audio_bytes(self, fake_tts):
        """Test that fake returns audio bytes."""
        response = fake_tts.synthesize("Hello world", language="pl")
        
        assert isinstance(response.audio, bytes)
        assert len(response.audio) > 0

    def test_fake_returns_correct_language(self, fake_tts):
        """Test that fake returns the requested language."""
        response = fake_tts.synthesize("Hello", language="en")
        
        assert response.language == "en"

    def test_fake_with_custom_voice(self, fake_tts):
        """Test that fake accepts voice parameter."""
        response = fake_tts.synthesize("Hello", voice="nova")
        
        assert isinstance(response.audio, bytes)

    def test_fake_tracks_calls(self, fake_tts):
        """Test that fake tracks method calls."""
        fake_tts.synthesize("First text", language="pl")
        fake_tts.synthesize("Second text", language="en")
        
        calls = fake_tts.get_calls()
        assert len(calls) == 2

    def test_fake_assert_language(self, fake_tts):
        """Test language assertion helper."""
        fake_tts.synthesize("Polish text", language="pl")
        fake_tts.synthesize("English text", language="en")
        
        fake_tts.assert_synthesized_with_language("pl")
        fake_tts.assert_synthesized_with_language("en")

    def test_fake_assert_text(self, fake_tts):
        """Test text assertion helper."""
        fake_tts.synthesize("Hello world")
        
        fake_tts.assert_synthesized_text("Hello world")

    def test_fake_reset(self, fake_tts):
        """Test that reset clears call history."""
        fake_tts.synthesize("Text 1")
        fake_tts.synthesize("Text 2")
        
        fake_tts.reset()
        
        assert len(fake_tts.get_calls()) == 0

    def test_fake_duration_based_on_text(self, fake_tts):
        """Test that fake generates audio proportional to text length."""
        short_text = "Hi"
        long_text = "This is a much longer text that should generate more audio"
        
        short_response = fake_tts.synthesize(short_text)
        long_response = fake_tts.synthesize(long_text)
        
        assert long_response.duration_seconds > short_response.duration_seconds


class TestFakeTTSValidation:
    """Test validation logic using fake."""

    def test_fake_handles_empty_text(self):
        """Test that fake handles empty text gracefully."""
        fake = FakeTTSService()
        
        response = fake.synthesize("")
        
        assert response.audio is not None

    def test_fake_handles_unicode_text(self):
        """Test that fake handles Polish unicode text."""
        fake = FakeTTSService()
        
        fake.synthesize("To jest polski tekst z polskimi znakami: ąęźż")
        
        assert "polski" in fake.get_synthesized_texts()[0].lower()
