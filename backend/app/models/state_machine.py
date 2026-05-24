"""State machine models for whitebox test modeling (FR 4.0)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.test_case import TestCase


class CoverageCriterion(str, Enum):
    """Coverage goals for state-based test sequence planning."""

    ALL_STATES = "ALL_STATES"
    ALL_TRANSITIONS = "ALL_TRANSITIONS"


class StateTransitionTuple(BaseModel):
    """Five-tuple (state, event, guard, action, next_state) for one transition edge."""

    state: str = Field(description="Source state")
    event: str = Field(description="Triggering event or input")
    guard: Optional[str] = Field(default=None, description="Guard condition, if any")
    action: Optional[str] = Field(default=None, description="Action executed on transition")
    next_state: str = Field(description="Target state after transition")

    def transition_id(self) -> str:
        """Return a stable transition identifier for coverage tracking."""
        event_label = self.event
        if self.guard:
            event_label = f"{event_label}[{self.guard}]"
        if self.action:
            event_label = f"{event_label}/{self.action}"
        return f"{self.state}--{event_label}-->{self.next_state}"


class StateMachineModel(BaseModel):
    """Directed state machine extracted from a structured requirement."""

    initial_state: str = Field(description="Entry state")
    states: list[str] = Field(default_factory=list, description="All states in the model")
    transitions: list[StateTransitionTuple] = Field(
        default_factory=list, description="Directed transition edges"
    )
    mermaid_diagram: str = Field(
        default="", description="stateDiagram-v2 Mermaid source for visualization"
    )
    id: Optional[str] = Field(default=None, description="Persisted model identifier")
    requirement_id: Optional[str] = Field(
        default=None, description="Source requirement reference"
    )
    revision: int = Field(default=0, ge=0, description="Revision for human review workflow")


class TestSequence(BaseModel):
    """A planned event/state path achieving a coverage criterion."""

    sequence_id: str = Field(description="Unique sequence identifier")
    steps: list[str] = Field(
        default_factory=list, description="Ordered events or actions to execute"
    )
    covered_items: list[str] = Field(
        default_factory=list,
        description="States or transition IDs covered by this sequence",
    )
    derived_test_cases: list[TestCase] = Field(
        default_factory=list,
        description="Test cases mapped from this sequence (technique=StateTransition)",
    )
