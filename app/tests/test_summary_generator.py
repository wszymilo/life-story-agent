"""Tests for summary generator service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from services.summary_generator import (
    _generate_summary_text,
    _generate_title,
    _validate_grounding,
    generate_summary,
)


class MockResponse:
    def __init__(self, content: str):
        self.content = content


class MockChoice:
    def __init__(self, content: str):
        self.message = MagicMock(content=content)


class MockCompletion:
    def __init__(self, content: str):
        self.choices = [MockChoice(content)]


class MockParsedResult:
    def __init__(self, is_grounded: bool, reason: str = ""):
        self.is_grounded = is_grounded
        self.reason = reason


class MockChoiceParsed:
    def __init__(self, is_grounded: bool, reason: str = ""):
        self.message = MagicMock(parsed=MockParsedResult(is_grounded, reason))


class MockCompletionParsed:
    def __init__(self, is_grounded: bool, reason: str = ""):
        self.choices = [MockChoiceParsed(is_grounded, reason)]


class TestGenerateSummaryUnit:
    """Unit tests for summary generator - testing each function separately."""

    @pytest.mark.asyncio
    async def test_generate_summary_text(self):
        """Test generator creates summary text."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=MockCompletion("This is my life story summary.")
        )

        result = await _generate_summary_text(
            mock_client,
            "I was born in 1950 in Warsaw.",
            "pl"
        )

        assert "life story" in result.lower()
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_grounding_grounded(self):
        """Test reviewer approves grounded summary."""
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=MockCompletionParsed(True, "")
        )

        is_grounded, reason = await _validate_grounding(
            mock_client,
            "I was born in Warsaw.",
            "I was born in Warsaw. I had a dog.",
            "pl"
        )

        assert is_grounded is True
        mock_client.beta.chat.completions.parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_grounding_not_grounded(self):
        """Test reviewer rejects ungrounded summary."""
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=MockCompletionParsed(False, "Contains facts not in source")
        )

        is_grounded, reason = await _validate_grounding(
            mock_client,
            "I was born in Krakow.",  # Different from source
            "I was born in Warsaw.",
            "pl"
        )

        assert is_grounded is False

    @pytest.mark.asyncio
    async def test_generate_title(self):
        """Test title generation."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=MockCompletion("Childhood in Warsaw")
        )

        result = await _generate_title(
            mock_client,
            "I was born in 1950 in Warsaw...",
            "pl"
        )

        assert "Warsaw" in result

    @pytest.mark.asyncio
    async def test_generate_title_fallback_on_error(self):
        """Test fallback title on error."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API error")
        )

        result = await _generate_title(mock_client, "summary", "pl")

        assert result == "My Life Story"


class TestGenerateSummaryIntegration:
    """Integration tests for full summary generation flow."""

    @pytest.mark.asyncio
    async def test_generate_summary_with_transcripts(self):
        """Test summary generation with transcripts only."""
        from services import summary_generator
        original_client = summary_generator.AsyncOpenAI

        mock_client = AsyncMock()

        async def mock_create(*args, **kwargs):
            messages = args[0] if args else kwargs.get("messages", [])
            prompt = messages[0].get("content", "") if messages else ""

            if "title" in prompt.lower():
                return MockCompletion("My Test Title")
            else:
                return MockCompletion("This is my test summary about growing up.")

        mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=MockCompletionParsed(True, "")
        )
        summary_generator.AsyncOpenAI = lambda api_key: mock_client

        try:
            result = await generate_summary(
                transcripts=["I was born in Warsaw in 1950."],
                questions_and_answers=[],
                language="pl"
            )

            # Verify it got our mocked response
            assert "summary" in result.model_dump()
            assert result.title == "My Test Title"
            assert result.was_retried is False

        finally:
            summary_generator.AsyncOpenAI = original_client

    @pytest.mark.asyncio
    async def test_generate_summary_retries_on_failure(self):
        """Test that summary retries on grounding failure."""
        from services import summary_generator
        original_client = summary_generator.AsyncOpenAI

        mock_client = AsyncMock()
        parse_call_count = 0

        async def mock_create(*args, **kwargs):
            messages = args[0] if args else kwargs.get("messages", [])
            prompt = messages[0].get("content", "") if messages else ""

            if "title" in prompt.lower():
                return MockCompletion("Test Title")
            else:
                return MockCompletion("Test summary content")

        async def mock_parse(*args, **kwargs):
            nonlocal parse_call_count
            parse_call_count += 1
            if parse_call_count <= 1:
                return MockCompletionParsed(False, "Not grounded")
            return MockCompletionParsed(True, "")

        mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)
        mock_client.beta.chat.completions.parse = AsyncMock(side_effect=mock_parse)
        summary_generator.AsyncOpenAI = lambda api_key: mock_client

        try:
            result = await generate_summary(
                transcripts=["Test transcript"],
                questions_and_answers=[{"question": "Test?", "answer": "Test answer."}],
                language="pl"
            )

            # Should have retried (was_retried should be true because first validation returns false)
            assert result.was_retried is True

        finally:
            summary_generator.AsyncOpenAI = original_client

    @pytest.mark.asyncio
    async def test_generate_summary_requires_content(self):
        """Test that empty content raises error."""
        with pytest.raises(ValueError, match="No content"):
            await generate_summary(
                transcripts=[],
                questions_and_answers=[],
                language="pl"
            )


class TestGenerateSummaryTitleEdgeCases:
    """Edge case tests for title generation."""

    @pytest.mark.asyncio
    async def test_title_truncates_long_titles(self):
        """Test that very long titles are truncated."""
        mock_client = AsyncMock()
        long_title = "A" * 200
        mock_client.chat.completions.create = AsyncMock(
            return_value=MockCompletion(long_title)
        )

        result = await _generate_title(mock_client, "summary", "pl")

        assert len(result) <= 100

    @pytest.mark.asyncio
    async def test_title_handles_quotes(self):
        """Test that quotes are stripped from title."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=MockCompletion('"My Life Story"')
        )

        result = await _generate_title(mock_client, "summary", "pl")

        assert '"' not in result
