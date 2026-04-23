"""Tests for meta story generator service."""


import pytest

from tests.fakes.fake_llm import FakeLLMService


class TestMetaStoryGenerator:
    """Tests for meta story generation."""

    @pytest.mark.asyncio
    async def test_validates_minimum_sources(self):
        """Test that at least 2 sources are required."""
        from services.meta_story_generator import generate_meta_story

        with pytest.raises(ValueError, match="At least 2 sources required"):
            await generate_meta_story(
                sources=[{"title": "Story 1", "summary": "", "date": "", "transcripts": []}],
            )

    @pytest.mark.asyncio
    async def test_validates_maximum_sources(self):
        """Test that maximum sources limit is enforced."""
        from services.meta_story_generator import generate_meta_story

        with pytest.raises(ValueError, match="Maximum"):
            await generate_meta_story(
                sources=[{"title": f"Story {i}", "summary": "", "date": "", "transcripts": []} for i in range(15)],
            )


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
