"""Integration test for oracle CoT chain (mocked)."""

from __future__ import annotations

from typing import Any

from app.engines.oracle_synthesizer.synthesizer import DefaultOracleSynthesizer
from app.models.requirement import StructuredRequirement
from app.models.test_case import TestCase


class MockLLM:
    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        return {
            "reasoning_steps": [
                "Parse credentials from test_data.",
                "Apply valid credential condition.",
                "Map to authenticate and show dashboard.",
            ],
            "expected_result": "User is authenticated and dashboard is displayed.",
            "confidence": 0.9,
        }


def test_oracle_synthesize_with_mock_cot(login_requirement: StructuredRequirement) -> None:
    case = TestCase(
        id="tc-1",
        requirement_id=login_requirement.id,
        title="Valid login",
        test_steps=["Enter valid username/password", "Click login"],
        test_data="user=alice; password=secret",
        technique="StateTransition",
    )
    synthesizer = DefaultOracleSynthesizer(llm=MockLLM())
    oracle = synthesizer.synthesize(login_requirement, case)
    assert oracle.expected_result
    assert len(oracle.reasoning_steps) >= 3
    assert oracle.status == "pending_review"
