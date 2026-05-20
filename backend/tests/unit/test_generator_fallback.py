"""Generator fallback and replan tests."""

from app.engines.whitebox_modeler.generator import DefaultStateModelGenerator, replan_from_model
from app.models.requirement import StructuredRequirement
from app.models.state_machine import CoverageCriterion, StateMachineModel, StateTransitionTuple


def test_generate_without_llm_uses_fallback(login_requirement: StructuredRequirement) -> None:
    generator = DefaultStateModelGenerator()
    model, sequences, cases = generator.generate(
        login_requirement,
        coverage=CoverageCriterion.ALL_STATES,
        use_llm=False,
    )
    assert model.initial_state == "Initial"
    assert sequences
    assert cases[0].technique == "StateTransition"


def test_replan_from_model(small_machine: StateMachineModel) -> None:
    requirement = StructuredRequirement(
        id="r1",
        raw_text="triangle",
        input_fields=[],
        conditions=[],
        expected_actions=[],
    )
    sequences, cases = replan_from_model(
        requirement,
        small_machine,
        CoverageCriterion.ALL_TRANSITIONS,
    )
    assert sequences
    assert cases
