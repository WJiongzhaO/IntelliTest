"""Unit tests for Mermaid rendering."""

from app.engines.whitebox_modeler.mermaid_renderer import ensure_mermaid, render_mermaid
from app.models.state_machine import StateMachineModel, StateTransitionTuple


def test_render_mermaid_contains_states() -> None:
    model = StateMachineModel(
        initial_state="A",
        states=["A", "B"],
        transitions=[
            StateTransitionTuple(
                state="A", event="go", guard="ok", action="run", next_state="B"
            )
        ],
        mermaid_diagram="",
    )
    diagram = render_mermaid(model)
    assert "stateDiagram-v2" in diagram
    assert "[*] --> A" in diagram
    assert "A --> B" in diagram


def test_ensure_mermaid_fills_empty() -> None:
    model = StateMachineModel(
        initial_state="A",
        states=["A"],
        transitions=[],
        mermaid_diagram="",
    )
    filled = ensure_mermaid(model)
    assert filled.mermaid_diagram
