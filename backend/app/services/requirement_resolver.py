"""Resolve StructuredRequirement from inline payload or member A's database."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import RequirementModel
from app.models.requirement import StructuredRequirement
from app.repositories.memory_store import store


async def resolve_structured_requirement(
    db: AsyncSession,
    *,
    requirement_id: str | None = None,
    inline: StructuredRequirement | None = None,
) -> StructuredRequirement:
    """Load requirement from inline body, memory cache, or SQLite (FR 1.x / 2.0)."""
    if inline is not None:
        store.requirements[inline.id] = inline
        return inline

    if not requirement_id:
        raise HTTPException(status_code=400, detail="requirement or requirement_id required")

    cached = store.requirements.get(requirement_id)
    if isinstance(cached, StructuredRequirement):
        return cached

    model = await db.get(RequirementModel, requirement_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Requirement {requirement_id} not found")

    structured = _from_db_model(model)
    store.requirements[structured.id] = structured
    return structured


def _from_db_model(model: RequirementModel) -> StructuredRequirement:
    return StructuredRequirement(
        id=model.id,
        title=model.title,
        raw_text=model.raw_text,
        input_fields=list(model.input_fields or []),
        data_ranges=list(model.data_ranges or []),
        conditions=list(model.conditions or []),
        expected_actions=list(model.expected_actions or []),
        risk_score=model.risk_score,
        priority=model.priority,
    )
