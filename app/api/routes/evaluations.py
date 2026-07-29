from api.deps import CurrentUser, get_current_user
from api.logging_config import get_logger
from api.schemas.evaluation import (
    DashboardStats,
    EvaluationResultResponse,
    EvaluationScoresStore,
    EvaluationScores,
)
from config import get_settings
from db.deps import get_evaluation_repo
from db.repositories import EvaluationRepository
from fastapi import APIRouter, Depends, HTTPException
from services.evaluation import store_evaluation_scores

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])
logger = get_logger()
settings = get_settings()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    eval_type: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    evaluation_repo: EvaluationRepository = Depends(get_evaluation_repo),
):
    if current_user.email != settings.admin_email:
        raise HTTPException(403, "Admin access only")

    results = await evaluation_repo.fetch_recent(eval_type, limit=10)

    if not results:
        return DashboardStats(
            total_evaluations=0,
            avg_factual_accuracy=None,
            avg_coherence=None,
            avg_completeness=None,
            avg_overall_score=None,
            recent_evaluations=[],
        )

    recent = [EvaluationResultResponse(**r) for r in results]

    total = len(results)

    avg_factual = sum(r.get("factual_accuracy", 0) for r in results if r.get("factual_accuracy")) / total if total > 0 else None
    avg_coherence = sum(r.get("coherence", 0) for r in results if r.get("coherence")) / total if total > 0 else None
    avg_completeness = sum(r.get("completeness", 0) for r in results if r.get("completeness")) / total if total > 0 else None
    avg_overall = sum(r.get("overall_score", 0) for r in results if r.get("overall_score")) / total if total > 0 else None

    total_count = await evaluation_repo.count(eval_type)

    return DashboardStats(
        total_evaluations=total_count or 0,
        avg_factual_accuracy=round(avg_factual, 1) if avg_factual else None,
        avg_coherence=round(avg_coherence, 1) if avg_coherence else None,
        avg_completeness=round(avg_completeness, 1) if avg_completeness else None,
        avg_overall_score=round(avg_overall, 1) if avg_overall else None,
        recent_evaluations=recent,
    )


@router.post("/scores")
async def store_scores(
    data: EvaluationScoresStore,
    current_user: CurrentUser = Depends(get_current_user),
):
    scores = EvaluationScores(
        factual_accuracy=data.factual_accuracy,
        coherence=data.coherence,
        completeness=data.completeness,
        overall_score=data.overall_score,
    )
    await store_evaluation_scores(data.event_id, data.eval_type, scores)
    return {"status": "stored"}
