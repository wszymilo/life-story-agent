from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""

    total_evaluations: int
    avg_factual_accuracy: Optional[float]
    avg_coherence: Optional[float]
    avg_completeness: Optional[float]
    avg_overall_score: Optional[float]
    recent_evaluations: list[EvaluationResultResponse]