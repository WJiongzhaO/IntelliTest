"""Orchestrate whitebox modeling: extract → build → plan → TestCase mapping."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.engines.whitebox_modeler.coverage_planner import (
    PlannedPath,
    plan_sequences,
    to_test_sequences,
)
from app.engines.whitebox_modeler.graph_builder import build_graph
from app.engines.whitebox_modeler.mermaid_renderer import ensure_mermaid
from app.engines.whitebox_modeler.tuple_extractor import extract_state_machine
from app.exceptions import WhiteboxModelError, IntelliTestError
from app.models.requirement import StructuredRequirement
from app.models.state_machine import (
    CoverageCriterion,
    StateMachineModel,
    StateTransitionTuple,
    TestSequence,
)
from app.models.test_case import Priority, TestCase
from app.services.llm_types import LLMClientProtocol
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class StateModelGenerator(Protocol):
    """Generator interface aligned with blackbox_generator convention."""

    def generate(
        self,
        requirement: StructuredRequirement,
        *,
        coverage: CoverageCriterion = CoverageCriterion.ALL_STATES,
        model: StateMachineModel | None = None,
        use_llm: bool = True,
    ) -> tuple[StateMachineModel, list[TestSequence], list[TestCase]]:
        ...


def _priority_from_requirement(requirement: StructuredRequirement) -> Priority:
    if requirement.priority:
        try:
            return Priority(requirement.priority)
        except ValueError:
            pass
    if requirement.risk_score and requirement.risk_score >= 15:
        return Priority.HIGH
    if requirement.risk_score and requirement.risk_score <= 8:
        return Priority.LOW
    return Priority.MEDIUM


def _paths_to_test_cases(
    requirement: StructuredRequirement,
    paths: list[PlannedPath],
    coverage: CoverageCriterion,
) -> list[TestCase]:
    priority = _priority_from_requirement(requirement)
    cases: list[TestCase] = []
    for index, path in enumerate(paths, start=1):
        test_data = ", ".join(path.event_steps) if path.event_steps else None
        cases.append(
            TestCase(
                id=f"tc-st-{uuid.uuid4().hex[:8]}",
                requirement_id=requirement.id,
                title=f"State transition path {index} ({coverage.value})",
                precondition=f"System in state: {path.state_path[0]}",
                test_steps=[f"State: {state}" for state in path.state_path],
                test_data=test_data,
                expected_result=None,
                technique="StateTransition",
                priority=priority,
                risk_score=requirement.risk_score,
                coverage_items=path.covered_items,
                modified_by_user=False,
            )
        )
    return cases


class DefaultStateModelGenerator:
    """Default FR 4.0 state model generator implementation."""

    def __init__(self, llm: LLMClientProtocol | None = None) -> None:
        self._llm = llm

    def generate(
        self,
        requirement: StructuredRequirement,
        *,
        coverage: CoverageCriterion = CoverageCriterion.ALL_STATES,
        model: StateMachineModel | None = None,
        use_llm: bool = True,
    ) -> tuple[StateMachineModel, list[TestSequence], list[TestCase]]:
        machine = model
        if machine is None:
            if use_llm:
                try:
                    machine = extract_state_machine(requirement, self._llm)
                except WhiteboxModelError:
                    raise
                except IntelliTestError as exc:
                    raise WhiteboxModelError(str(exc)) from exc
            else:
                machine = _fallback_model(requirement)

        machine = ensure_mermaid(machine)
        graph = build_graph(machine)
        paths = plan_sequences(graph, coverage)
        test_cases = _paths_to_test_cases(requirement, paths, coverage)
        sequences = to_test_sequences(paths)

        for sequence, case in zip(sequences, test_cases, strict=True):
            sequence.derived_test_cases = [case]

        logger.info(
            "State model generated nodes=%d sequences=%d cases=%d coverage_hits=%d",
            len(machine.states),
            len(sequences),
            len(test_cases),
            sum(len(c.coverage_items) for c in test_cases),
        )
        return machine, sequences, test_cases


def _fallback_model(requirement: StructuredRequirement) -> StateMachineModel:
    """Rule-based minimal model when LLM is unavailable."""
    return StateMachineModel(
        initial_state="Initial",
        states=["Initial", "Complete"],
        transitions=[
            StateTransitionTuple(
                state="Initial",
                event="execute",
                guard=None,
                action="process",
                next_state="Complete",
            )
        ],
        mermaid_diagram="",
        requirement_id=requirement.id,
    )


def replan_from_model(
    requirement: StructuredRequirement,
    model: StateMachineModel,
    coverage: CoverageCriterion,
) -> tuple[list[TestSequence], list[TestCase]]:
    """Recompute sequences and test cases after manual model edits."""
    machine = ensure_mermaid(model)
    graph = build_graph(machine)
    paths = plan_sequences(graph, coverage)
    test_cases = _paths_to_test_cases(requirement, paths, coverage)
    sequences = to_test_sequences(paths)
    for sequence, case in zip(sequences, test_cases, strict=True):
        sequence.derived_test_cases = [case]
    return sequences, test_cases


StateModelGenerator = DefaultStateModelGenerator
