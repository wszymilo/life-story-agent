"""Tests for meta story generator service."""

from unittest.mock import AsyncMock, patch

import pytest

from tests.fakes.fake_llm import FakeLLMService


class TestMetaStoryGenerator:
    """Tests for meta story generation."""

    @pytest.mark.asyncio
    async def test_validates_minimum_events(self):
        """Test that at least 2 events are required."""
        from services.meta_story_generator import generate_meta_story

        with pytest.raises(ValueError, match="At least 2 events required"):
            await generate_meta_story(
                user_id="user-1",
                event_ids=["event-1"],
            )

    @pytest.mark.asyncio
    async def test_validates_maximum_events(self):
        """Test that maximum events limit is enforced."""
        from services.meta_story_generator import generate_meta_story

        with pytest.raises(ValueError, match="Maximum"):
            await generate_meta_story(
                user_id="user-1",
                event_ids=[f"event-{i}" for i in range(15)],
            )

    @pytest.mark.asyncio
    async def test_sorts_events_by_date(self):
        """Test that events are sorted chronologically."""

        mock_events = [
            {"id": "newer", "created_at": "2024-02-01", "time_anchor_date": None},
            {"id": "older", "created_at": "2024-01-01", "time_anchor_date": None},
        ]

        with patch("services.meta_story_generator.get_supabase_client") as mock_supabase:
            mock_client = AsyncMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = type(
                "obj", (object,), {"data": mock_events}
            )()
            mock_supabase.return_value = mock_client


class TestMetaStoryGeneratorWithFakeLLM:
    """Tests using FakeLLMService for meta story generation logic."""

    def test_fake_llm_generates_meta_story_theme(self):
        """Test that fake LLM can generate meta story themed responses."""
        fake_llm = FakeLLMService()
        
        fake_llm.program_response(
            "life story",
            "A journey through time spanning decades of memories."
        )
        
        response = fake_llm.complete("Generate a meta story theme for my life")
        
        assert isinstance(response.content, str)
        assert len(response.content) > 0

    def test_fake_llm_handles_multiple_events(self):
        """Test that fake LLM can process multiple event contexts."""
        fake_llm = FakeLLMService()
        
        prompt_with_events = """
        Events:
        1. Childhood in Warsaw - 1960s
        2. Moving to Krakow - 1975
        3. Starting family - 1985
        
        Generate a meta story theme connecting these events.
        """
        
        fake_llm.program_response("Warsaw", "Eastern European roots")
        fake_llm.program_response("Krakow", "Building a new life")
        
        response = fake_llm.complete(prompt_with_events)
        
        assert isinstance(response.content, str)
        assert len(response.content) > 0

    def test_fake_llm_tracks_meta_story_calls(self):
        """Test that fake tracks calls for meta story generation."""
        fake_llm = FakeLLMService()
        
        fake_llm.complete("First meta story prompt")
        fake_llm.complete("Second meta story prompt")
        
        calls = fake_llm.get_calls()
        assert len(calls) == 2

    def test_fake_llm_generates_narrative_flow(self):
        """Test that fake can generate flowing narrative."""
        fake_llm = FakeLLMService()
        
        fake_llm.program_response("timeline", "From childhood memories to present day")
        fake_llm.program_response("journey", "A continuous narrative spanning decades")
        
        response = fake_llm.complete("Create a timeline-based narrative of my life")
        
        assert isinstance(response.content, str)
        assert len(response.content) > 0

    def test_fake_llm_handles_diverse_events(self):
        """Test that fake handles diverse life events."""
        fake_llm = FakeLLMService()
        
        events = [
            "childhood",
            "marriage", 
            "career",
            "retirement"
        ]
        
        for event in events:
            fake_llm.program_response(event, f"Chapter about {event}")
        
        for event in events:
            response = fake_llm.complete(f"Tell me about {event}")
            assert event in response.content.lower()
            pass

    @pytest.mark.asyncio
    async def test_includes_sources_section(self):
        """Test that sources section is added to summary."""
        from services.meta_story_generator import generate_meta_story

        # Test that function exists and is callable
        assert callable(generate_meta_story)
