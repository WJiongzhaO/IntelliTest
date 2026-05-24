"""Unit tests for state graph builder."""

import pytest

from app.engines.whitebox_modeler.graph_builder import build_graph
from app.exceptions import WhiteboxModelError
from app.models.state_machine import StateMachineModel, StateTransitionTuple


def test_build_valid_graph(small_machine: StateMachineModel) -> None:
    graph = build_graph(small_machine)
    assert graph.initial_state == "S0"
    assert len(graph.states) == 3


def test_unreachable_state_raises() -> None:
    model = StateMachineModel(
        initial_state="A",
        states=["A", "B"],
        transitions=[],
        mermaid_diagram="",
    )
    with pytest.raises(WhiteboxModelError, match="Unreachable"):
        build_graph(model)


def test_duplicate_transition_raises() -> None:
    transition = StateTransitionTuple(
        state="A", event="go", guard=None, action=None, next_state="B"
    )
    model = StateMachineModel(
        initial_state="A",
        states=["A", "B"],
        transitions=[transition, transition],
        mermaid_diagram="",
    )
    with pytest.raises(WhiteboxModelError, match="Duplicate"):
        build_graph(model)


def test_guarded_duplicate_events_are_valid_branches() -> None:
    model = StateMachineModel(
        initial_state="PendingPayment",
        states=["PendingPayment", "PaymentCreated", "PaymentRejected"],
        transitions=[
            StateTransitionTuple(
                state="PendingPayment",
                event="clickPayNow",
                guard="order is payable",
                action="create payment flow",
                next_state="PaymentCreated",
            ),
            StateTransitionTuple(
                state="PendingPayment",
                event="clickPayNow",
                guard="order is cancelled or amount invalid",
                action="show error",
                next_state="PaymentRejected",
            ),
        ],
        mermaid_diagram="",
    )

    graph = build_graph(model)

    assert len(graph.outgoing("PendingPayment")) == 2


def test_invalid_initial_state_raises() -> None:
    model = StateMachineModel(
        initial_state="Z",
        states=["A", "B"],
        transitions=[
            StateTransitionTuple(
                state="A", event="go", guard=None, action=None, next_state="B"
            )
        ],
        mermaid_diagram="",
    )
    with pytest.raises(WhiteboxModelError, match="initial_state"):
        build_graph(model)
