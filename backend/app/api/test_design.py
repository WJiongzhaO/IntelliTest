"""Combined test design pipeline API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engines.workflow.test_design_pipeline import run_combined_pipeline
from app.models.requirement import StructuredRequirement
from app.models.state_machine import CoverageCriterion
from app.models.test_case import TestCase, TestSuite
from app.repositories.memory_store import store

router = APIRouter()


class CombinedDesignRequest(BaseModel):
    requirement_id: Optional[str] = None
    requirement: Optional[StructuredRequirement] = None
    techniques: list[str] = Field(default_factory=lambda: ["StateTransition"])
    coverage: CoverageCriterion = CoverageCriterion.ALL_TRANSITIONS
    synthesize_oracles: bool = True
    use_llm: bool = True
    blackbox_cases: list[TestCase] = Field(default_factory=list)


@router.post("/combined", response_model=TestSuite)
def combined_design(body: CombinedDesignRequest) -> TestSuite:
    if body.requirement:
        requirement = body.requirement
    elif body.requirement_id:
        stored = store.requirements.get(body.requirement_id)
        if isinstance(stored, StructuredRequirement):
            requirement = stored
        else:
            requirement = StructuredRequirement(
                id=body.requirement_id,
                raw_text=f"Requirement {body.requirement_id}",
                input_fields=[],
                conditions=[],
                expected_actions=[],
            )
    else:
        raise HTTPException(status_code=400, detail="requirement or requirement_id required")

    store.requirements[requirement.id] = requirement
    return run_combined_pipeline(
        requirement,
        techniques=body.techniques,
        coverage=body.coverage,
        synthesize_oracles=body.synthesize_oracles,
        blackbox_cases=body.blackbox_cases or None,
        use_llm=body.use_llm,
    )
