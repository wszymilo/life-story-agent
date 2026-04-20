from datetime import date
from typing import Optional

from pydantic import BaseModel


class SummaryWithTitle(BaseModel):
    """Final output from summary generator."""

    summary: str
    title: str
    was_retried: bool = False
    """Whether the summary was regenerated due to grounding issues"""

    time_anchor_date: Optional[date] = None
    """Extracted primary date from the story (YYYY-MM-DD format)"""