"""Rule-based oracle consistency validation without LLM."""

from __future__ import annotations

from app.models.requirement import StructuredRequirement
from app.models.test_case import TestCase

_CONTRADICTION_PAIRS = [
    ("success", "fail"),
    ("pass", "fail"),
    ("accept", "reject"),
    ("valid", "invalid"),
    ("allow", "deny"),
    ("enabled", "disabled"),
]


def validate_oracle(
    requirement: StructuredRequirement,
    test_case: TestCase,
    expected_result: str,
) -> tuple[bool, list[str]]:
    """Return (consistent, validation_messages)."""
    messages: list[str] = []
    normalized = expected_result.lower().strip()

    if not normalized:
        messages.append("expected_result is empty")
        return False, messages

    for left, right in _CONTRADICTION_PAIRS:
        if left in normalized and right in normalized:
            messages.append(f"Contradictory terms detected: {left} vs {right}")

    if requirement.expected_actions:
        action_hits = sum(
            1
            for action in requirement.expected_actions
            if _token_overlap(action.lower(), normalized) >= 0.2
        )
        if action_hits == 0:
            messages.append(
                "expected_result has low overlap with requirement expected_actions"
            )

    consistent = not messages
    return consistent, messages


def _token_overlap(left: str, right: str) -> float:
    left_tokens = {token for token in left.split() if len(token) > 2}
    right_tokens = {token for token in right.split() if len(token) > 2}
    if not left_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)
