"""FR 7.0 — Test suite optimization API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.engines.suite_optimizer.optimizer import OptimizationMetrics, OptimizationStrategy, optimize_suite
from app.models.test_case import TestCase

router = APIRouter(prefix="/suites", tags=["Suite Optimization"])


class OptimizeSuiteRequest(BaseModel):
    """Optimize a batch of test cases supplied by caller (e.g. future FR 3.0 output)."""

    test_cases: list[TestCase] = Field(description="Candidate test cases")
    strategy: OptimizationStrategy = Field(
        default="risk_then_minimize",
        description="risk_sort | minimize_coverage | risk_then_minimize",
    )
    coverage_universe: list[str] | None = Field(
        default=None,
        description="Optional explicit coverage item IDs; default is union of case coverage_items",
    )


class OptimizeSuiteResponse(BaseModel):
    optimized_test_cases: list[TestCase]
    metrics: OptimizationMetrics


@router.post("/optimize", response_model=OptimizeSuiteResponse)
async def optimize_suite_endpoint(body: OptimizeSuiteRequest):
    """Prioritize by risk and/or greedily shrink suite while targeting coverage items."""
    optimized, metrics = optimize_suite(
        body.test_cases,
        body.strategy,
        coverage_universe=body.coverage_universe,
    )
    return OptimizeSuiteResponse(optimized_test_cases=optimized, metrics=metrics)
