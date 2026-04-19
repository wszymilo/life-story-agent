from typing import Optional

from pydantic import BaseModel


class GeneratedSummary(BaseModel):
    """Structured output for generated summary."""

    summary: str
    """The generated narrative summary"""

    title: str
    """Generated title for the event"""

    is_grounded: bool
    """Whether the summary is grounded in the source material"""

    grounding_notes: Optional[str] = None
    """Notes from reviewer about grounding (if not grounded)"""


class SummaryWithTitle(BaseModel):
    """Final output from summary generator."""

    summary: str
    title: str
    was_retried: bool = False
    """Whether the summary was regenerated due to grounding issues"""
