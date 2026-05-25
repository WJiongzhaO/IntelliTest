"""FR 1.0 / 1.1 — Requirements management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.engines.input_parser.parser import parse_csv, parse_form, parse_text
from app.engines.requirement_structurer.structurer import (
    StructuringError,
    structure_requirement,
)
from app.engines.risk_analyzer.analyzer import RiskAnalysisError, analyze_requirement_risk
from app.models.db_models import RequirementModel
from app.models.risk import RiskAssessment
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/requirements", tags=["Requirements"])


# ─── Request / Response schemas ────────────────────────────────────────


class TextInputRequest(BaseModel):
    text: str = Field(description="Freeform text with one or more requirements")
    title: Optional[str] = Field(default=None, description="Requirement title")


class FormEntry(BaseModel):
    title: str = Field(min_length=1, description="Requirement title")
    raw_text: str = Field(description="Single requirement description")


class FormInputRequest(BaseModel):
    entries: list[FormEntry] = Field(description="List of requirement entries")


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    raw_text: Optional[str] = None
    input_fields: Optional[list[str]] = None
    data_ranges: Optional[list[str]] = None
    conditions: Optional[list[str]] = None
    expected_actions: Optional[list[str]] = None


class RequirementResponse(BaseModel):
    id: str
    title: Optional[str] = None
    raw_text: str
    source_type: str
    input_fields: list[str]
    data_ranges: list[str]
    conditions: list[str]
    expected_actions: list[str]
    is_structured: bool
    risk_impact: Optional[int] = None
    risk_likelihood: Optional[int] = None
    risk_score: Optional[int] = None
    priority: Optional[str] = None
    risk_impact_rationale: Optional[str] = None
    risk_likelihood_rationale: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Helpers ───────────────────────────────────────────────────────────


def _to_response(model: RequirementModel) -> RequirementResponse:
    return RequirementResponse(
        id=model.id,
        title=model.title,
        raw_text=model.raw_text,
        source_type=model.source_type,
        input_fields=model.input_fields or [],
        data_ranges=model.data_ranges or [],
        conditions=model.conditions or [],
        expected_actions=model.expected_actions or [],
        is_structured=model.is_structured,
        risk_impact=model.risk_impact,
        risk_likelihood=model.risk_likelihood,
        risk_score=model.risk_score,
        priority=model.priority,
        risk_impact_rationale=model.risk_impact_rationale,
        risk_likelihood_rationale=model.risk_likelihood_rationale,
        created_at=model.created_at.isoformat() if model.created_at else None,
        updated_at=model.updated_at.isoformat() if model.updated_at else None,
    )


def _clean_title(value: object) -> str | None:
    if value is None:
        return None
    title = str(value).strip()
    return title or None


def _apply_text_title(items: list[dict], title: str | None) -> list[dict]:
    cleaned = _clean_title(title)
    if not cleaned:
        return items
    if len(items) <= 1:
        return [{**item, "title": cleaned} for item in items]
    return [
        {**item, "title": cleaned if index == 0 else f"{cleaned} {index + 1}"}
        for index, item in enumerate(items)
    ]


async def _store_parsed(
    db: AsyncSession,
    items: list[dict],
    source_type: str,
) -> list[RequirementModel]:
    models: list[RequirementModel] = []
    for item in items:
        model = RequirementModel(
            title=_clean_title(item.get("title")),
            raw_text=item["raw_text"],
            source_type=source_type,
        )
        db.add(model)
        models.append(model)
    await db.commit()
    for m in models:
        await db.refresh(m)
    logger.info("Stored %d requirements from %s", len(models), source_type)
    return models


# ─── Create ────────────────────────────────────────────────────────────


@router.post("/upload", response_model=list[RequirementResponse])
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """FR 1.0 — Upload a CSV file of requirements."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are accepted")

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb}MB limit")

    parsed = parse_csv(content, file.filename)
    if len(parsed) == 0:
        raise HTTPException(400, "No requirements found in the CSV file")

    models = await _store_parsed(db, list(parsed), "csv")
    return [_to_response(m) for m in models]


@router.post("/text", response_model=list[RequirementResponse])
async def ingest_text(
    body: TextInputRequest,
    db: AsyncSession = Depends(get_db),
):
    """FR 1.0 — Parse freeform text into requirements."""
    parsed = _apply_text_title(list(parse_text(body.text)), body.title)
    models = await _store_parsed(db, parsed, "text")
    return [_to_response(m) for m in models]


@router.post("", response_model=list[RequirementResponse])
async def ingest_form(
    body: FormInputRequest,
    db: AsyncSession = Depends(get_db),
):
    """FR 1.0 — Direct form/structured input."""
    parsed = parse_form([e.model_dump() for e in body.entries])
    models = await _store_parsed(db, list(parsed), "form")
    return [_to_response(m) for m in models]


# ─── Read ──────────────────────────────────────────────────────────────


@router.get("", response_model=list[RequirementResponse])
async def list_requirements(db: AsyncSession = Depends(get_db)):
    """List all requirements ordered by creation time descending."""
    result = await db.execute(
        select(RequirementModel).order_by(RequirementModel.created_at.desc())
    )
    models = result.scalars().all()
    return [_to_response(m) for m in models]


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single requirement by ID."""
    model = await db.get(RequirementModel, requirement_id)
    if not model:
        raise HTTPException(404, f"Requirement {requirement_id} not found")
    return _to_response(model)


# ─── Update ────────────────────────────────────────────────────────────


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: str,
    body: RequirementUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Manually update a requirement's fields."""
    model = await db.get(RequirementModel, requirement_id)
    if not model:
        raise HTTPException(404, f"Requirement {requirement_id} not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)

    await db.commit()
    await db.refresh(model)
    return _to_response(model)


# ─── Delete ────────────────────────────────────────────────────────────


@router.delete("/{requirement_id}")
async def delete_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a requirement."""
    model = await db.get(RequirementModel, requirement_id)
    if not model:
        raise HTTPException(404, f"Requirement {requirement_id} not found")
    await db.delete(model)
    await db.commit()
    return {"detail": f"Requirement {requirement_id} deleted"}


# ─── Structure ──────────────────────────────────────────────────────────


@router.post("/{requirement_id}/structure", response_model=RequirementResponse)
async def structure_single_requirement(
    requirement_id: str,
    db: AsyncSession = Depends(get_db),
):
    """FR 1.1 — Trigger LLM-based structuring for a specific requirement."""
    model = await db.get(RequirementModel, requirement_id)
    if not model:
        raise HTTPException(404, f"Requirement {requirement_id} not found")

    try:
        structured = await structure_requirement(model.id, model.raw_text, model.title)
    except StructuringError as exc:
        raise HTTPException(422, str(exc)) from exc

    model.input_fields = structured.input_fields
    model.data_ranges = structured.data_ranges
    model.conditions = structured.conditions
    model.expected_actions = structured.expected_actions
    model.is_structured = True

    await db.commit()
    await db.refresh(model)
    return _to_response(model)


@router.post("/{requirement_id}/risk", response_model=RiskAssessment)
async def analyze_risk_for_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """FR 2.0 — LLM-assisted risk scoring and priority (persisted on requirement)."""
    model = await db.get(RequirementModel, requirement_id)
    if not model:
        raise HTTPException(404, f"Requirement {requirement_id} not found")

    try:
        assessment = await analyze_requirement_risk(
            model.id,
            model.raw_text,
            input_fields=model.input_fields or [],
            data_ranges=model.data_ranges or [],
            conditions=model.conditions or [],
            expected_actions=model.expected_actions or [],
        )
    except RiskAnalysisError as exc:
        raise HTTPException(422, str(exc)) from exc

    model.risk_impact = assessment.impact
    model.risk_likelihood = assessment.likelihood
    model.risk_score = assessment.risk_score
    model.priority = assessment.priority
    model.risk_impact_rationale = assessment.impact_rationale
    model.risk_likelihood_rationale = assessment.likelihood_rationale

    await db.commit()
    await db.refresh(model)
    return assessment.model_copy(update={"requirement_title": model.title})
