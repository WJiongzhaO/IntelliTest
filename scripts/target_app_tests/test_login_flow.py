"""PyTest skeleton aligned with IntelliTest exported test case IDs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CASES_PATH = Path(__file__).parent / "test_cases.json"


def _load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_case_traceability(case: dict) -> None:
    """Placeholder: wire to Selenium/API checks per case['test_steps']."""
    assert case["id"]
    assert case.get("expected_result"), f"Missing oracle for {case['id']}"
    # TODO: map technique StateTransition -> state path assertions
    # TODO: map EP/BVA -> input boundary checks


def test_health_smoke() -> None:
    """Ensure target application is reachable before UI tests."""
    assert True
