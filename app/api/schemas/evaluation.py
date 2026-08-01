import uuid
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


class QuestionEvaluationScores(BaseModel):
    """Structured output from question quality evaluation."""

    relevance: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    open_endedness: int = Field(ge=1, le=5)
    diversity: int = Field(ge=1, le=5)
    expected_richness: int = Field(ge=1, le=5)
    overall_score: int = Field(ge=1, le=5)
    explanation: str = Field(default="")


class EvaluationScoresStore(BaseModel):
    """Input for storing pre-computed evaluation scores."""

    event_id: uuid.UUID
    eval_type: str
    factual_accuracy: int = Field(ge=1, le=5)
    coherence: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    overall_score: int = Field(ge=1, le=5)


class EvaluationResultResponse(BaseModel):
    """Response for evaluation result (scores only)."""

    id: uuid.UUID
    event_id: uuid.UUID
    eval_type: str
    factual_accuracy: Optional[int]
    coherence: Optional[int]
    completeness: Optional[int]
    overall_score: Optional[int]
    evaluator_model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""

    total_evaluations: int
    avg_factual_accuracy: Optional[float]
    avg_coherence: Optional[float]
    avg_completeness: Optional[float]
    avg_overall_score: Optional[float]
    recent_evaluations: list[EvaluationResultResponse]
