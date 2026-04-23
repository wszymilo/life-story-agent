from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvaluationScores(BaseModel):
    """Structured output from LLM-as-judge evaluation."""

    factual_accuracy: int = Field(ge=1, le=5)
    coherence: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    overall_score: int = Field(ge=1, le=5)
    explanation: str = Field(default="")


class EvaluationResultCreate(BaseModel):
    """Input for creating an evaluation result."""

    event_id: str
    eval_type: str
    prompt_text: Optional[str] = None
    summary_text: Optional[str] = None
    factual_accuracy: Optional[int] = None
    coherence: Optional[int] = None
    completeness: Optional[int] = None
    overall_score: Optional[int] = None
    evaluator_model: str = "gpt-4o"


class EvaluationResultResponse(BaseModel):
    """Response for evaluation result."""

    id: str
    event_id: str
    eval_type: str
    prompt_text: Optional[str]
    summary_text: Optional[str]
    factual_accuracy: Optional[int]
    coherence: Optional[int]
    completeness: Optional[int]
    overall_score: Optional[int]
    evaluator_model: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_row(cls, row: dict) -> "EvaluationResultResponse":
        """Create an EvaluationResultResponse from a Supabase row dict."""
        return cls(
            id=row["id"],
            event_id=row["event_id"],
            eval_type=row["eval_type"],
            prompt_text=row.get("prompt_text"),
            summary_text=row.get("summary_text"),
            factual_accuracy=row.get("factual_accuracy"),
            coherence=row.get("coherence"),
            completeness=row.get("completeness"),
            overall_score=row.get("overall_score"),
            evaluator_model=row.get("evaluator_model", "gpt-4o"),
            created_at=row["created_at"],
        )


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""

    total_evaluations: int
    avg_factual_accuracy: Optional[float]
    avg_coherence: Optional[float]
    avg_completeness: Optional[float]
    avg_overall_score: Optional[float]
    recent_evaluations: list[EvaluationResultResponse]