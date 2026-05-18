"""Integration test for whitebox LLM extraction chain (mocked)."""

from __future__ import annotations

from typing import Any

from app.engines.whitebox_modeler.generator import DefaultStateModelGenerator
from app.engines.whitebox_modeler.tuple_extractor import extract_state_machine
from app.models.requirement import StructuredRequirement
from app.models.state_machine import CoverageCriterion


class MockLLM:
    def complete_json(
        self, system: str, user: str, *, temperature: float | None = None
    ) -> dict[str, Any]:
      return {
          "initial_state": "Idle",
          "states": ["Idle", "Active"],
          "transitions": [
              {
                  "state": "Idle",
                  "event": "login",
                  "guard": "valid",
                  "action": "auth",
                  "next_state": "Active",
              }
          ],
          "mermaid_diagram": "stateDiagram-v2\n  [*] --> Idle",
      }


def test_extract_and_generate_with_mock_llm(login_requirement: StructuredRequirement) -> None:
    llm = MockLLM()
    model = extract_state_machine(login_requirement, llm)
    assert model.initial_state == "Idle"
    assert len(model.states) == 2

    generator = DefaultStateModelGenerator(llm=llm)
    machine, sequences, cases = generator.generate(
        login_requirement,
        coverage=CoverageCriterion.ALL_TRANSITIONS,
        model=model,
        use_llm=False,
    )
    assert machine.initial_state == "Idle"
    assert sequences
    assert cases
    assert cases[0].technique == "StateTransition"
