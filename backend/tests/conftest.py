"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from app.models.requirement import StructuredRequirement
from app.models.state_machine import StateMachineModel, StateTransitionTuple


@pytest.fixture
def login_requirement() -> StructuredRequirement:
    return StructuredRequirement(
        id="req-login",
        raw_text="User logs in and logs out.",
        input_fields=["username", "password"],
        data_ranges=[],
        conditions=["valid credentials"],
        expected_actions=["authenticate", "show dashboard", "clear session"],
    )


@pytest.fixture
def small_machine() -> StateMachineModel:
    return StateMachineModel(
        initial_state="S0",
        states=["S0", "S1", "S2"],
        transitions=[
            StateTransitionTuple(
                state="S0", event="a", guard=None, action=None, next_state="S1"
            ),
            StateTransitionTuple(
                state="S1", event="b", guard=None, action=None, next_state="S2"
            ),
            StateTransitionTuple(
                state="S2", event="c", guard=None, action=None, next_state="S0"
            ),
        ],
        mermaid_diagram="",
    )
