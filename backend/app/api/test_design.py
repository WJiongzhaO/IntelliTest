"""Combined test design pipeline API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.engines.workflow.test_design_pipeline import run_combined_pipeline
from app.exceptions import WhiteboxModelError
from app.models.requirement import StructuredRequirement
from app.models.state_machine import CoverageCriterion
from app.models.test_case import TestCase, TestSuite
from app.repositories.memory_store import store
from app.services.artifact_store import persist_suite
from app.services.requirement_resolver import resolve_structured_requirement

router = APIRouter()


class CombinedDesignRequest(BaseModel):
    requirement_id: Optional[str] = None
    requirement: Optional[StructuredRequirement] = None
    techniques: list[str] = Field(
        default_factory=lambda: ["EP", "BVA", "DT", "StateTransition"]
    )
    coverage: CoverageCriterion = CoverageCriterion.ALL_TRANSITIONS
    synthesize_oracles: bool = True
    use_llm: bool = True
    blackbox_cases: list[TestCase] = Field(default_factory=list)


@router.post("/combined", response_model=TestSuite)
async def combined_design(
    body: CombinedDesignRequest,
    db: AsyncSession = Depends(get_db),
) -> TestSuite:
    """Run blackbox (C) + whitebox (D) + optional oracle synthesis (D) in one suite."""
    requirement = await resolve_structured_requirement(
        db,
        requirement_id=body.requirement_id,
        inline=body.requirement,
    )

    try:
        suite = run_combined_pipeline(
            requirement,
            techniques=body.techniques,
            coverage=body.coverage,
            synthesize_oracles=body.synthesize_oracles,
            blackbox_cases=body.blackbox_cases or None,
            use_llm=body.use_llm,
        )
    except WhiteboxModelError as exc:
        status_code = 502 if body.use_llm else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    store.last_suite_id = suite.id
    for case in suite.test_cases:
        store.test_cases[case.id] = case

    persist_id = body.requirement_id
    if persist_id:
        await persist_suite(
            db,
            requirement_id=persist_id,
            suite=suite,
            source_type="combined",
        )
    return suite
