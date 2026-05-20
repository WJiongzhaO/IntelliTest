"""Render stateDiagram-v2 Mermaid text from a state machine model."""

from __future__ import annotations

from app.models.state_machine import StateMachineModel, StateTransitionTuple


def render_mermaid(model: StateMachineModel) -> str:
    """Generate Mermaid stateDiagram-v2 from transitions."""
    lines = ["stateDiagram-v2", f"  [*] --> {model.initial_state}"]
    for transition in model.transitions:
        label = _edge_label(transition)
        lines.append(f"  {transition.state} --> {transition.next_state}: {label}")
    return "\n".join(lines)


def _edge_label(transition: StateTransitionTuple) -> str:
    parts = [transition.event]
    if transition.guard:
        parts.append(f"[{transition.guard}]")
    if transition.action:
        parts.append(f"/ {transition.action}")
    return " ".join(parts)


def ensure_mermaid(model: StateMachineModel) -> StateMachineModel:
    """Fill or repair mermaid_diagram when empty or inconsistent."""
    if model.mermaid_diagram.strip():
        return model
    return model.model_copy(update={"mermaid_diagram": render_mermaid(model)})
