"""PyTest skeleton aligned with IntelliTest exported test case IDs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CASES_PATH = Path(__file__).parent / "test_cases.json"


def _load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["test_case_id"])
def test_case_traceability(case: dict) -> None:
    """Each optimized export row must carry a test oracle for automation mapping."""
    assert case["test_case_id"]
    assert case.get("expected_result"), f"Missing oracle for {case['test_case_id']}"
    assert case.get("requirement_id", "").startswith("LR-")


def test_health_smoke() -> None:
    from juice_shop_client import health_check

    assert health_check(), "Juice Shop must be running (default http://localhost:3001)"
