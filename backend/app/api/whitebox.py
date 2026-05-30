"""FR 4.0 whitebox modeling API routes."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.engines.whitebox_modeler.generator import DefaultStateModelGenerator, replan_from_model
from app.engines.whitebox_modeler.mermaid_renderer import ensure_mermaid, render_mermaid
from app.exceptions import WhiteboxModelError
from app.models.requirement import StructuredRequirement
from app.models.state_machine import (
    CoverageCriterion,
    StateMachineModel,
    StateTransitionTuple,
    TestSequence,
)
from app.models.test_case import TestCase
from app.repositories.memory_store import store
from app.services.artifact_store import persist_whitebox
from app.services.requirement_resolver import resolve_structured_requirement

router = APIRouter()


class WhiteboxModelRequest(BaseModel):
    requirement_id: Optional[str] = None
    requirement: Optional[StructuredRequirement] = None
    coverage: CoverageCriterion = CoverageCriterion.ALL_STATES
    use_llm: bool = True


class WhiteboxModelResponse(BaseModel):
    model: StateMachineModel
    sequences: list[TestSequence]
    test_cases: list[TestCase]
    coverage: CoverageCriterion


class MermaidRegenerateRequest(BaseModel):
    initial_state: str
    states: list[str]
    transitions: list[StateTransitionTuple]


class MermaidRegenerateResponse(BaseModel):
    mermaid_diagram: str


class WhiteboxModelUpdate(BaseModel):
    initial_state: Optional[str] = None
    states: Optional[list[str]] = None
    transitions: Optional[list[StateTransitionTuple]] = None
    mermaid_diagram: Optional[str] = None
    coverage: CoverageCriterion = CoverageCriterion.ALL_STATES


def _register_cases(cases: list[TestCase]) -> None:
    for case in cases:
        store.test_cases[case.id] = case


@router.post("/model", response_model=WhiteboxModelResponse)
async def create_whitebox_model(
    body: WhiteboxModelRequest,
    db: AsyncSession = Depends(get_db),
) -> WhiteboxModelResponse:
    """Extract state machine, plan coverage sequences, and map test cases."""
    requirement = await resolve_structured_requirement(
        db,
        requirement_id=body.requirement_id,
        inline=body.requirement,
    )
    generator = DefaultStateModelGenerator()

    try:
        model, sequences, test_cases = generator.generate(
            requirement,
            coverage=body.coverage,
            use_llm=body.use_llm,
        )
    except WhiteboxModelError as exc:
        if not body.use_llm:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            model, sequences, test_cases = generator.generate(
                requirement,
                coverage=body.coverage,
                use_llm=False,
            )
        except WhiteboxModelError as retry_exc:
            raise HTTPException(status_code=502, detail=str(retry_exc)) from retry_exc

    model_id = model.id or f"wm-{uuid.uuid4().hex[:8]}"
    model = model.model_copy(
        update={"id": model_id, "requirement_id": requirement.id},
    )
    store.whitebox_models[model_id] = model
    _register_cases(test_cases)

    persist_id = body.requirement_id
    if persist_id:
        await persist_whitebox(
            db,
            requirement_id=persist_id,
            suite_name=f"Whitebox model for {requirement.id}",
            test_cases=test_cases,
            payload={
                "model": model.model_dump(),
                "sequences": [seq.model_dump() for seq in sequences],
                "coverage": body.coverage.value,
            },
        )

    return WhiteboxModelResponse(
        model=model,
        sequences=sequences,
        test_cases=test_cases,
        coverage=body.coverage,
    )


@router.get("/model/{model_id}", response_model=StateMachineModel)
async def get_whitebox_model(model_id: str) -> StateMachineModel:
    model = store.whitebox_models.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/model/{model_id}", response_model=WhiteboxModelResponse)
async def update_whitebox_model(
    model_id: str,
    body: WhiteboxModelUpdate,
    db: AsyncSession = Depends(get_db),
) -> WhiteboxModelResponse:
    existing = store.whitebox_models.get(model_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")

    updated = existing.model_copy(
        update={
            k: v
            for k, v in body.model_dump(exclude_unset=True, exclude={"coverage"}).items()
            if v is not None
        }
    )
    updated = updated.model_copy(update={"revision": existing.revision + 1})
    updated = ensure_mermaid(updated)

    if updated.requirement_id:
        requirement = await resolve_structured_requirement(
            db,
            requirement_id=updated.requirement_id,
        )
    else:
        cached = store.requirements.get("unknown")
        requirement = (
            cached
            if isinstance(cached, StructuredRequirement)
            else StructuredRequirement(
                id="unknown",
                raw_text="",
                input_fields=[],
                conditions=[],
                expected_actions=[],
            )
        )

    sequences, test_cases = replan_from_model(requirement, updated, body.coverage)
    store.whitebox_models[model_id] = updated
    _register_cases(test_cases)

    return WhiteboxModelResponse(
        model=updated,
        sequences=sequences,
        test_cases=test_cases,
        coverage=body.coverage,
    )


@router.post("/regenerate-mermaid", response_model=MermaidRegenerateResponse)
async def regenerate_mermaid(body: MermaidRegenerateRequest) -> MermaidRegenerateResponse:
    model = StateMachineModel(
        initial_state=body.initial_state,
        states=body.states,
        transitions=body.transitions,
        mermaid_diagram="",
    )
    return MermaidRegenerateResponse(mermaid_diagram=render_mermaid(model))
