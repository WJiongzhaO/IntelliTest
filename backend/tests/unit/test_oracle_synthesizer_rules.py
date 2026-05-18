"""Oracle synthesizer rule-based path tests."""

from app.engines.oracle_synthesizer.synthesizer import DefaultOracleSynthesizer
from app.models.requirement import StructuredRequirement
from app.models.test_case import TestCase


def test_synthesize_without_llm() -> None:
    requirement = StructuredRequirement(
        id="r1",
        raw_text="Action",
        expected_actions=["System shows confirmation"],
    )
    case = TestCase(
        id="tc1",
        requirement_id="r1",
        title="Confirm",
        test_steps=["submit form"],
    )
    oracle = DefaultOracleSynthesizer().synthesize(requirement, case, use_llm=False)
    assert oracle.expected_result == "System shows confirmation"
    assert oracle.reasoning_steps
