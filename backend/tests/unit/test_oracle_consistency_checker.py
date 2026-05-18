"""Unit tests for oracle consistency checker."""

from app.engines.oracle_synthesizer.consistency_checker import validate_oracle
from app.models.requirement import StructuredRequirement
from app.models.test_case import TestCase


def test_contradiction_detected() -> None:
    requirement = StructuredRequirement(
        id="r1",
        raw_text="Login flow",
        expected_actions=["show dashboard"],
    )
    case = TestCase(
        id="tc1",
        requirement_id="r1",
        title="Login",
        test_steps=["submit valid credentials"],
    )
    consistent, messages = validate_oracle(
        requirement,
        case,
        "Login success and login fail simultaneously",
    )
    assert not consistent
    assert any("Contradictory" in message for message in messages)


def test_aligned_expected_action() -> None:
    requirement = StructuredRequirement(
        id="r1",
        raw_text="Login flow",
        expected_actions=["show dashboard to user"],
    )
    case = TestCase(
        id="tc1",
        requirement_id="r1",
        title="Login",
        test_steps=["submit valid credentials"],
    )
    consistent, messages = validate_oracle(
        requirement,
        case,
        "Dashboard is shown to the user after authentication.",
    )
    assert consistent
    assert not messages
