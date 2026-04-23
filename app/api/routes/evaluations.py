"""Evaluation routes for dashboard."""

import hashlib

from api.deps import CurrentUser, get_current_user
from api.logging_config import get_logger
from api.schemas.evaluation import DashboardStats, EvaluationResultCreate, EvaluationResultResponse
from config import get_settings
from db.client import get_supabase_client
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])
logger = get_logger()
settings = get_settings()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    eval_type: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get evaluation dashboard statistics (admin only).

    Args:
        eval_type: Optional filter by evaluation type (summary, meta_story, question).
                   Defaults to all types.
    """
    if current_user.email != settings.admin_email:
        raise HTTPException(403, "Admin access only")

    supabase = await get_supabase_client()

    query = supabase.table("evaluation_results").select("*")
    if eval_type:
        query = query.eq("eval_type", eval_type)

    results = query.order("created_at", desc=True).limit(10).execute()

    if not results.data:
        return DashboardStats(
            total_evaluations=0,
            avg_factual_accuracy=None,
            avg_coherence=None,
            avg_completeness=None,
            avg_overall_score=None,
            recent_evaluations=[],
        )

    recent = [EvaluationResultResponse.from_row(r) for r in results.data]

    total = len(results.data)

    avg_factual = sum(r.get("factual_accuracy", 0) for r in results.data if r.get("factual_accuracy")) / total if total > 0 else None
    avg_coherence = sum(r.get("coherence", 0) for r in results.data if r.get("coherence")) / total if total > 0 else None
    avg_completeness = sum(r.get("completeness", 0) for r in results.data if r.get("completeness")) / total if total > 0 else None
    avg_overall = sum(r.get("overall_score", 0) for r in results.data if r.get("overall_score")) / total if total > 0 else None

    count_query = supabase.table("evaluation_results").select("count", count="exact")
    if eval_type:
        count_query = count_query.eq("eval_type", eval_type)
    count_result = count_query.execute()
    total_count = count_result.count or 0

    return DashboardStats(
        total_evaluations=total_count,
        avg_factual_accuracy=round(avg_factual, 1) if avg_factual else None,
        avg_coherence=round(avg_coherence, 1) if avg_coherence else None,
        avg_completeness=round(avg_completeness, 1) if avg_completeness else None,
        avg_overall_score=round(avg_overall, 1) if avg_overall else None,
        recent_evaluations=recent,
    )


@router.post("", response_model=EvaluationResultResponse)
async def create_evaluation(
    eval_data: EvaluationResultCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new evaluation result."""
    supabase = await get_supabase_client()

    data = eval_data.model_dump()
    data["prompt_hash"] = hashlib.sha256(data.get("prompt_text", "").encode()).hexdigest()[:16]

    result = supabase.table("evaluation_results").insert(data).execute()

    if not result.data:
        raise HTTPException(500, "Failed to create evaluation")

    return EvaluationResultResponse.from_row(result.data[0])
