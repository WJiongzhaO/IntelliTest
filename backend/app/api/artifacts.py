"""Review artifacts API — load/save persisted test design outputs."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import RequirementModel
from app.models.test_case import CoverageItem, TestCase, TestSuite
from app.services.artifact_store import load_review_bundles, save_review_bundle

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


class RequirementReviewBundle(BaseModel):
    requirement_id: str
    external_id: Optional[str] = None
    title: Optional[str] = None
    requirement_ref: str
    suite: Optional[TestSuite] = None
    test_cases: list[TestCase] = Field(default_factory=list)
    coverage_items: list[CoverageItem] = Field(default_factory=list)


class ReviewArtifactsResponse(BaseModel):
    bundles: list[RequirementReviewBundle]


class ReviewBundleSaveRequest(BaseModel):
    requirement_id: str
    test_cases: list[TestCase]
    coverage_items: list[CoverageItem] = Field(default_factory=list)


@router.get("/review", response_model=ReviewArtifactsResponse)
async def get_review_artifacts(db: AsyncSession = Depends(get_db)) -> ReviewArtifactsResponse:
    """Load persisted test cases grouped by requirement for the review page."""
    raw = await load_review_bundles(db)
    bundles = [RequirementReviewBundle(**item) for item in raw]
    return ReviewArtifactsResponse(bundles=bundles)


@router.put("/review/{requirement_id}")
async def save_review_bundle_endpoint(
    requirement_id: str,
    body: ReviewBundleSaveRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Persist human-reviewed test cases and coverage for one requirement."""
    model = await db.get(RequirementModel, requirement_id)
    if model is None:
        raise HTTPException(404, f"Requirement {requirement_id} not found")

    await save_review_bundle(
        db,
        internal_req_id=requirement_id,
        test_cases=body.test_cases,
        coverage_items=body.coverage_items,
    )
    return {"detail": "Review bundle saved"}
