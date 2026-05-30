"""Helpers for requirement business identifiers."""

from __future__ import annotations

from app.models.db_models import RequirementModel


def requirement_ref_id(model: RequirementModel) -> str:
    """Return the stable business id (e.g. LR-001) when present, else internal id."""
    external = (model.external_id or "").strip()
    return external or model.id
