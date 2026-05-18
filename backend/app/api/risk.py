"""FR 2.0 — Risk dashboard API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import RequirementModel
from app.models.risk import RiskAssessment, RiskDashboardSummary

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.get("/dashboard", response_model=RiskDashboardSummary)
async def risk_dashboard(
    top_n: int = Query(default=5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate risk metrics for dashboard widgets."""
    total_q = await db.execute(select(func.count()).select_from(RequirementModel))
    total_requirements = int(total_q.scalar_one())

    analyzed_stmt = select(RequirementModel).where(RequirementModel.risk_score.is_not(None))
    analyzed_result = await db.execute(analyzed_stmt)
    analyzed_rows = analyzed_result.scalars().all()
    analyzed_count = len(analyzed_rows)

    priority_high = sum(1 for r in analyzed_rows if r.priority == "High")
    priority_medium = sum(1 for r in analyzed_rows if r.priority == "Medium")
    priority_low = sum(1 for r in analyzed_rows if r.priority == "Low")

    average_risk_score: float | None = None
    if analyzed_count:
        average_risk_score = sum(r.risk_score or 0 for r in analyzed_rows) / analyzed_count

    sorted_rows = sorted(
        analyzed_rows,
        key=lambda r: (r.risk_score or 0, r.id),
        reverse=True,
    )[:top_n]

    highest_risk: list[RiskAssessment] = []
    for r in sorted_rows:
        if r.risk_impact is None or r.risk_likelihood is None or r.risk_score is None:
            continue
        highest_risk.append(
            RiskAssessment(
                requirement_id=r.id,
                impact=r.risk_impact,
                likelihood=r.risk_likelihood,
                risk_score=r.risk_score,
                priority=r.priority or "Low",
                impact_rationale=r.risk_impact_rationale or "",
                likelihood_rationale=r.risk_likelihood_rationale or "",
            )
        )

    return RiskDashboardSummary(
        total_requirements=total_requirements,
        analyzed_count=analyzed_count,
        priority_high=priority_high,
        priority_medium=priority_medium,
        priority_low=priority_low,
        average_risk_score=average_risk_score,
        highest_risk=highest_risk,
    )
