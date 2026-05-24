"""Unit tests for coverage planning."""

from app.engines.whitebox_modeler.coverage_planner import plan_sequences
from app.engines.whitebox_modeler.graph_builder import build_graph
from app.models.state_machine import CoverageCriterion, StateMachineModel, StateTransitionTuple


def _triangle_graph() -> StateMachineModel:
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


def test_all_states_covers_every_state() -> None:
    graph = build_graph(_triangle_graph())
    paths = plan_sequences(graph, CoverageCriterion.ALL_STATES)
    covered = set()
    for path in paths:
        covered.update(path.covered_items)
    assert covered == {"S0", "S1", "S2"}


def test_all_transitions_covers_every_edge() -> None:
    graph = build_graph(_triangle_graph())
    paths = plan_sequences(graph, CoverageCriterion.ALL_TRANSITIONS)
    covered = set()
    for path in paths:
        covered.update(path.covered_items)
    expected = {"S0--a-->S1", "S1--b-->S2", "S2--c-->S0"}
    assert expected <= covered


def test_all_states_sequence_count_reasonable() -> None:
    graph = build_graph(_triangle_graph())
    paths = plan_sequences(graph, CoverageCriterion.ALL_STATES)
    assert 1 <= len(paths) <= 3


def test_all_transitions_distinguishes_guarded_duplicate_events() -> None:
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
    paths = plan_sequences(graph, CoverageCriterion.ALL_TRANSITIONS)
    covered = {item for path in paths for item in path.covered_items}

    assert "PendingPayment--clickPayNow[order is payable]/create payment flow-->PaymentCreated" in covered
    assert (
        "PendingPayment--clickPayNow[order is cancelled or amount invalid]/show error-->PaymentRejected"
        in covered
    )
