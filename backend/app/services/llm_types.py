"""LLM client protocol without heavy dependencies."""

from __future__ import annotations

from typing import Any, Protocol


class LLMClientProtocol(Protocol):
    """Protocol for swapping LLM implementations in tests."""

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Return parsed JSON object from the model response."""
        ...
