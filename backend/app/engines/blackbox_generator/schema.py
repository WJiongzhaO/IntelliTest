"""Parse and validate LLM black-box test design JSON into domain models."""

from __future__ import annotations

from typing import Any

from app.exceptions import BlackboxGenerationError
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, CoverageItem, Priority, TestCase

_VALID_TECHNIQUES = frozenset({"EP", "BVA", "DT"})
_PRIORITY_MAP = {
    "HIGH": Priority.HIGH,
    "MEDIUM": Priority.MEDIUM,
    "LOW": Priority.LOW,
}


def validate_blackbox_payload(
    payload: dict[str, Any],
    *,
    requested_techniques: list[BlackBoxTechnique],
) -> None:
    """Raise BlackboxGenerationError if the LLM response is incomplete or invalid."""
    if "test_cases" not in payload:
        raise BlackboxGenerationError("LLM response missing 'test_cases'")

    cases = payload["test_cases"]
    if not isinstance(cases, list) or len(cases) == 0:
        raise BlackboxGenerationError("LLM returned empty test_cases")

    techniques_found: set[str] = set()
    for idx, raw in enumerate(cases):
        if not isinstance(raw, dict):
            raise BlackboxGenerationError(f"test_cases[{idx}] is not an object")
        technique = str(raw.get("technique", "")).upper()
        if technique not in _VALID_TECHNIQUES:
            raise BlackboxGenerationError(
                f"test_cases[{idx}] has invalid technique: {technique!r}"
            )
        techniques_found.add(technique)
        _validate_test_case_fields(raw, idx)

    requested = {t.value for t in requested_techniques}
    missing = requested - techniques_found
    if missing:
        analysis = payload.get("analysis") or {}
        if "BVA" in missing and analysis.get("bva_applicable") is False:
            missing.discard("BVA")
        if missing:
            raise BlackboxGenerationError(
                f"LLM response missing requested techniques: {sorted(missing)}"
            )


def _validate_test_case_fields(raw: dict[str, Any], idx: int) -> None:
    for field in ("title", "test_steps", "expected_result"):
        if not raw.get(field):
            raise BlackboxGenerationError(
                f"test_cases[{idx}] missing required field '{field}'"
            )
    steps = raw["test_steps"]
    if not isinstance(steps, list) or len(steps) == 0:
        raise BlackboxGenerationError(f"test_cases[{idx}] test_steps must be non-empty list")


def parse_coverage_items(
    payload: dict[str, Any],
    requirement: StructuredRequirement,
) -> list[CoverageItem]:
    """Parse optional LLM coverage items; fall back to empty list."""
    raw_items = payload.get("coverage_items")
    if not isinstance(raw_items, list):
        return []

    items: list[CoverageItem] = []
    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            continue
        item_id = str(raw.get("id") or f"CI_{requirement.id}_llm_{idx}")
        techniques_raw = raw.get("selected_techniques") or []
        techniques: list[BlackBoxTechnique] = []
        for t in techniques_raw:
            try:
                techniques.append(BlackBoxTechnique(str(t).upper()))
            except ValueError:
                continue
        items.append(
            CoverageItem(
                id=item_id,
                requirement_id=requirement.id,
                description=str(raw.get("description") or ""),
                item_type=str(raw.get("item_type") or "general"),
                selected_techniques=techniques,
                covered_by_test_cases=[],
            )
        )
    return items


def parse_test_cases(
    payload: dict[str, Any],
    requirement: StructuredRequirement,
    *,
    requested_techniques: list[BlackBoxTechnique],
) -> list[TestCase]:
    """Validate payload and convert test_cases to TestCase models."""
    validate_blackbox_payload(payload, requested_techniques=requested_techniques)

    counters: dict[str, int] = {t.value: 0 for t in BlackBoxTechnique}
    result: list[TestCase] = []

    for raw in payload["test_cases"]:
        technique = BlackBoxTechnique(str(raw["technique"]).upper())
        counters[technique.value] += 1
        index = counters[technique.value]

        priority_raw = str(raw.get("priority") or requirement.priority or "Medium")
        priority = _PRIORITY_MAP.get(priority_raw.upper(), Priority.MEDIUM)

        coverage_raw = raw.get("coverage_items") or []
        coverage_ids = [str(c) for c in coverage_raw] if isinstance(coverage_raw, list) else []

        result.append(
            TestCase(
                id=f"{requirement.id}_{technique.value}_{index:03d}",
                requirement_id=requirement.id,
                title=str(raw["title"]),
                precondition=raw.get("precondition"),
                test_steps=[str(s) for s in raw["test_steps"]],
                test_data=raw.get("test_data"),
                expected_result=str(raw["expected_result"]),
                technique=technique,
                priority=priority,
                risk_score=requirement.risk_score,
                coverage_items=coverage_ids,
            )
        )

    return result
