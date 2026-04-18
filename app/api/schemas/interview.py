from typing import Optional

from pydantic import BaseModel


class TranscriptAnalysis(BaseModel):
    """Structured output for transcript analysis."""

    extracted_time: Optional[str] = None
    """Time reference mentioned in transcript (e.g., '1956', 'March 1956')"""

    extracted_place: Optional[str] = None
    """Place mentioned in transcript (e.g., 'Warsaw', 'my grandmother's house')"""

    people: list[str] = []
    """List of people mentioned in the transcript"""

    key_events: list[str] = []
    """List of key events or stories mentioned"""

    themes: list[str] = []
    """Main themes identified in the transcript"""

    summary: str
    """Brief summary of what the transcript is about"""


class FollowUpQuestion(BaseModel):
    """Structured output for follow-up question generation."""

    question_text: str
    """The generated follow-up question"""

    question_type: str
    """Type of question: sensory, emotional, people, context, detail"""

    context: str
    """Why this question is relevant (based on transcript)"""

    target_area: str
    """Area the question explores: place, time, person, emotion, detail"""
