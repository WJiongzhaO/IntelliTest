"""In-memory persistence for whitebox models and oracle records."""

from __future__ import annotations

from app.models.oracle import OracleResult
from app.models.state_machine import StateMachineModel


class MemoryStore:
    """Thread-unsafe in-memory store suitable for development and tests."""

    def __init__(self) -> None:
        self.whitebox_models: dict[str, StateMachineModel] = {}
        self.oracles: dict[str, OracleResult] = {}
        self.requirements: dict[str, object] = {}


store = MemoryStore()
