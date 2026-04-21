"""Tests for interview agent using FakeLLMService."""

import pytest

from tests.fakes.fake_llm import FakeLLMService, LLMResponse


class TestFakeLLMService:
    """Tests for FakeLLMService."""

    @pytest.fixture
    def fake_llm(self):
        """Create a fake LLM service."""
        return FakeLLMService()

    def test_fake_returns_default_response(self, fake_llm):
        """Test that fake returns default response."""
        response = fake_llm.complete("test prompt")
        
        assert isinstance(response, LLMResponse)
        assert "testowa odpowiedź" in response.content

    def test_fake_with_programmed_response(self, fake_llm):
        """Test that fake returns programmed response."""
        fake_llm.program_response("follow-up", "Tell me more about your childhood.")
        
        response = fake_llm.complete("Generate a follow-up question")
        
        assert response.content == "Tell me more about your childhood."

    def test_fake_tracks_calls(self, fake_llm):
        """Test that fake tracks method calls."""
        fake_llm.complete("first prompt")
        fake_llm.complete("second prompt")
        
        calls = fake_llm.get_calls()
        assert len(calls) == 2

    def test_fake_multiple_programmed_responses(self, fake_llm):
        """Test multiple programmed responses work."""
        fake_llm.program_response("follow-up", "Follow-up response")
        fake_llm.program_response("analyze", "Analysis response")
        
        response1 = fake_llm.complete("Generate follow-up")
        response2 = fake_llm.complete("Analyze this transcript")
        
        assert response1.content == "Follow-up response"
        assert response2.content == "Analysis response"

    def test_fake_set_default_response(self, fake_llm):
        """Test setting custom default response."""
        fake_llm.set_default_response("Custom default response")
        
        response = fake_llm.complete("random prompt")
        
        assert response.content == "Custom default response"

    def test_fake_assert_prompt_contains(self, fake_llm):
        """Test prompt content assertion."""
        fake_llm.complete("This is a test prompt about childhood")
        
        fake_llm.assert_prompt_contains("childhood")

    def test_fake_reset(self, fake_llm):
        """Test reset clears calls and responses."""
        fake_llm.program_response("test", "response")
        fake_llm.complete("prompt")
        
        fake_llm.reset()
        
        assert len(fake_llm.get_calls()) == 0


class TestFakeLLMWithLanguage:
    """Test LLM fake handles language correctly."""

    def test_fake_returns_response_in_polish(self):
        """Test fake works with Polish prompts."""
        fake = FakeLLMService()
        fake.program_response("opowiedz", "Opowiedz więcej o swoim dzieciństwie.")
        
        response = fake.complete("Opowiedz mi o swoim dzieciństwie")
        
        assert "dzieciństwie" in response.content

    def test_fake_returns_response_in_english(self):
        """Test fake works with English prompts."""
        fake = FakeLLMService()
        fake.program_response("childhood", "Tell me more about your childhood.")
        
        response = fake.complete("Tell me about your childhood")
        
        assert "childhood" in response.content.lower()
