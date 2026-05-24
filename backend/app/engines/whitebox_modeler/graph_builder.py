"""Build and validate a directed state graph from transition tuples."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from app.exceptions import WhiteboxModelError
from app.models.state_machine import StateMachineModel, StateTransitionTuple


@dataclass
class StateGraph:
    """Adjacency representation of a state machine."""

    initial_state: str
    states: list[str]
    transitions: list[StateTransitionTuple]
    adjacency: dict[str, list[StateTransitionTuple]] = field(default_factory=dict)

    def outgoing(self, state: str) -> list[StateTransitionTuple]:
        return self.adjacency.get(state, [])


def build_graph(model: StateMachineModel) -> StateGraph:
    """Validate the model and return an adjacency graph."""
    if not model.states:
        raise WhiteboxModelError("State machine has no states")
    if model.initial_state not in model.states:
        raise WhiteboxModelError(
            f"initial_state '{model.initial_state}' is not in states list"
        )

    state_set = set(model.states)
    seen_edges: set[tuple[str, str, str, str, str]] = set()
    adjacency: dict[str, list[StateTransitionTuple]] = defaultdict(list)

    for transition in model.transitions:
        if transition.state not in state_set:
            raise WhiteboxModelError(f"Unknown source state: {transition.state}")
        if transition.next_state not in state_set:
            raise WhiteboxModelError(f"Unknown target state: {transition.next_state}")

        edge_key = (
            transition.state,
            transition.event,
            transition.guard or "",
            transition.action or "",
            transition.next_state,
        )
        if edge_key in seen_edges:
            raise WhiteboxModelError(f"Duplicate transition edge: {edge_key}")
        seen_edges.add(edge_key)

        adjacency[transition.state].append(transition)

    graph = StateGraph(
        initial_state=model.initial_state,
        states=list(model.states),
        transitions=list(model.transitions),
        adjacency=dict(adjacency),
    )

    _validate_reachability(graph)
    _warn_isolated(graph)
    return graph


def _validate_reachability(graph: StateGraph) -> None:
    """Ensure every state is reachable from the initial state."""
    visited = _bfs_states(graph, graph.initial_state)
    unreachable = set(graph.states) - visited
    if unreachable:
        raise WhiteboxModelError(
            f"Unreachable states from initial '{graph.initial_state}': "
            f"{sorted(unreachable)}"
        )


def _warn_isolated(graph: StateGraph) -> None:
    """Detect states with no incoming and no outgoing transitions (except initial-only)."""
    has_in = {graph.initial_state}
    has_out = set()
    for transition in graph.transitions:
        has_out.add(transition.state)
        has_in.add(transition.next_state)

    for state in graph.states:
        if state not in has_in and state not in has_out and state != graph.initial_state:
            raise WhiteboxModelError(f"Isolated state with no transitions: {state}")


def _bfs_states(graph: StateGraph, start: str) -> set[str]:
    visited: set[str] = set()
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for transition in graph.outgoing(current):
            if transition.next_state not in visited:
                queue.append(transition.next_state)
    return visited


def shortest_path_events(graph: StateGraph, start: str, goal: str) -> list[str]:
    """BFS shortest event sequence from start to goal state."""
    return [transition.event for transition in shortest_path_transitions(graph, start, goal)]


def shortest_path_transitions(
    graph: StateGraph,
    start: str,
    goal: str,
) -> list[StateTransitionTuple]:
    """BFS shortest transition sequence from start to goal state."""
    if start == goal:
        return []

    parent: dict[str, tuple[str, StateTransitionTuple]] = {}
    queue: deque[str] = deque([start])
    visited = {start}

    while queue:
        current = queue.popleft()
        for transition in graph.outgoing(current):
            nxt = transition.next_state
            if nxt in visited:
                continue
            parent[nxt] = (current, transition)
            if nxt == goal:
                return _reconstruct_transitions(parent, start, goal)
            visited.add(nxt)
            queue.append(nxt)

    raise WhiteboxModelError(f"No path from '{start}' to '{goal}'")


def _reconstruct_transitions(
    parent: dict[str, tuple[str, StateTransitionTuple]],
    start: str,
    goal: str,
) -> list[StateTransitionTuple]:
    transitions: list[StateTransitionTuple] = []
    node = goal
    while node != start:
        prev, transition = parent[node]
        transitions.append(transition)
        node = prev
    transitions.reverse()
    return transitions
