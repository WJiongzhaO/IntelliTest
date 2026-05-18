"""Coverage-driven test sequence planning for state machines."""

from __future__ import annotations

from dataclasses import dataclass

from app.engines.whitebox_modeler.graph_builder import StateGraph, shortest_path_events
from app.models.state_machine import CoverageCriterion, TestSequence
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class PlannedPath:
    """Internal path representation before TestCase mapping."""

    state_path: list[str]
    event_steps: list[str]
    covered_items: list[str]


def plan_sequences(
    graph: StateGraph,
    coverage: CoverageCriterion,
) -> list[PlannedPath]:
    """Plan one or more paths satisfying the coverage criterion."""
    if coverage == CoverageCriterion.ALL_STATES:
        paths = _plan_all_states(graph)
    else:
        paths = _plan_all_transitions(graph)

    logger.info(
        "Coverage plan criterion=%s sequences=%d",
        coverage.value,
        len(paths),
    )
    return paths


def to_test_sequences(paths: list[PlannedPath]) -> list[TestSequence]:
    """Convert planned paths to TestSequence shells (test cases added by generator)."""
    sequences: list[TestSequence] = []
    for index, path in enumerate(paths, start=1):
        sequences.append(
            TestSequence(
                sequence_id=f"seq-{index:03d}",
                steps=path.event_steps,
                covered_items=path.covered_items,
                derived_test_cases=[],
            )
        )
    return sequences


def _plan_all_states(graph: StateGraph) -> list[PlannedPath]:
    uncovered = set(graph.states) - {graph.initial_state}
    paths: list[PlannedPath] = []

    while uncovered:
        current_state = graph.initial_state
        state_path = [current_state]
        event_steps: list[str] = []
        covered: list[str] = [graph.initial_state]

        while uncovered:
            progressed = False
            for transition in graph.outgoing(current_state):
                if transition.next_state in uncovered:
                    event_steps.append(transition.event)
                    current_state = transition.next_state
                    state_path.append(current_state)
                    covered.append(current_state)
                    uncovered.remove(current_state)
                    progressed = True
                    break

            if progressed:
                continue

            if not uncovered:
                break

            target = min(uncovered, key=str)
            prefix_events = shortest_path_events(graph, current_state, target)
            if not prefix_events:
                break

            walk_state = current_state
            for event in prefix_events:
                transition = _find_transition(graph, walk_state, event)
                event_steps.append(event)
                walk_state = transition.next_state
                state_path.append(walk_state)
                if walk_state in uncovered:
                    covered.append(walk_state)
                    uncovered.remove(walk_state)
                current_state = walk_state

            if not progressed and prefix_events:
                continue
            break

        paths.append(
            PlannedPath(
                state_path=state_path,
                event_steps=event_steps,
                covered_items=covered,
            )
        )

    if not paths:
        paths.append(
            PlannedPath(
                state_path=[graph.initial_state],
                event_steps=[],
                covered_items=[graph.initial_state],
            )
        )

    return paths


def _plan_all_transitions(graph: StateGraph) -> list[PlannedPath]:
    uncovered = {t.transition_id() for t in graph.transitions}
    paths: list[PlannedPath] = []
    current_state = graph.initial_state

    while uncovered:
        state_path = [current_state]
        event_steps: list[str] = []
        covered: list[str] = []

        while True:
            fired = _fire_next_uncovered(graph, current_state, uncovered)
            if fired:
                transition, tid = fired
                event_steps.append(transition.event)
                current_state = transition.next_state
                state_path.append(current_state)
                covered.append(tid)
                uncovered.remove(tid)
                continue

            if not uncovered:
                break

            candidate = _nearest_uncovered_transition(graph, current_state, uncovered)
            if candidate is None:
                break

            prefix = shortest_path_events(graph, current_state, candidate.state)
            walk = current_state
            for event in prefix:
                tr = _find_transition(graph, walk, event)
                event_steps.append(event)
                walk = tr.next_state
                state_path.append(walk)
            current_state = walk

            transition, tid = _fire_next_uncovered(graph, current_state, uncovered) or (
                None,
                None,
            )
            if transition and tid:
                event_steps.append(transition.event)
                current_state = transition.next_state
                state_path.append(current_state)
                covered.append(tid)
                uncovered.remove(tid)
            else:
                break

        paths.append(
            PlannedPath(
                state_path=state_path,
                event_steps=event_steps,
                covered_items=covered,
            )
        )

        if uncovered:
            current_state = graph.initial_state

    if not paths:
        paths.append(
            PlannedPath(
                state_path=[graph.initial_state],
                event_steps=[],
                covered_items=[],
            )
        )

    return paths


def _fire_next_uncovered(
    graph: StateGraph,
    state: str,
    uncovered: set[str],
) -> tuple | None:
    for transition in graph.outgoing(state):
        tid = transition.transition_id()
        if tid in uncovered:
            return transition, tid
    return None


def _nearest_uncovered_transition(
    graph: StateGraph,
    current: str,
    uncovered: set[str],
) -> StateTransitionTuple | None:
    id_to_transition = {t.transition_id(): t for t in graph.transitions}
    for tid in sorted(uncovered):
        transition = id_to_transition[tid]
        try:
            shortest_path_events(graph, current, transition.state)
            return transition
        except Exception:
            continue
    if uncovered:
        return id_to_transition[sorted(uncovered)[0]]
    return None


def _find_transition(graph: StateGraph, state: str, event: str):
    from app.exceptions import WhiteboxModelError

    for transition in graph.outgoing(state):
        if transition.event == event:
            return transition
    raise WhiteboxModelError(f"No transition for state={state} event={event}")
