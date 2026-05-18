"""Shortest path and edge-case graph tests."""

import pytest

from app.engines.whitebox_modeler.graph_builder import build_graph, shortest_path_events
from app.exceptions import WhiteboxModelError
from app.models.state_machine import StateMachineModel, StateTransitionTuple


def test_shortest_path_events() -> None:
    model = StateMachineModel(
        initial_state="A",
        states=["A", "B", "C"],
        transitions=[
            StateTransitionTuple(
                state="A", event="x", guard=None, action=None, next_state="B"
            ),
            StateTransitionTuple(
                state="B", event="y", guard=None, action=None, next_state="C"
            ),
        ],
        mermaid_diagram="",
    )
    graph = build_graph(model)
    events = shortest_path_events(graph, "A", "C")
    assert events == ["x", "y"]


def test_no_path_raises() -> None:
    model = StateMachineModel(
        initial_state="A",
        states=["A", "B", "C"],
        transitions=[
            StateTransitionTuple(
                state="A", event="x", guard=None, action=None, next_state="B"
            ),
            StateTransitionTuple(
                state="A", event="y", guard=None, action=None, next_state="C"
            ),
        ],
        mermaid_diagram="",
    )
    graph = build_graph(model)
    with pytest.raises(WhiteboxModelError, match="No path"):
        shortest_path_events(graph, "B", "C")
