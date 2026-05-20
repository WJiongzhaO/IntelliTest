"""Integration test for combined test design pipeline."""

from app.engines.workflow.test_design_pipeline import run_combined_pipeline
from app.models.requirement import StructuredRequirement
from app.models.state_machine import CoverageCriterion


def test_combined_pipeline_blackbox_and_whitebox(login_requirement: StructuredRequirement) -> None:
    suite = run_combined_pipeline(
        login_requirement,
        techniques=["EP", "StateTransition"],
        coverage=CoverageCriterion.ALL_STATES,
        synthesize_oracles=False,
        use_llm=False,
    )
    assert suite.test_cases
    techniques = {str(c.technique) for c in suite.test_cases}
    assert "StateTransition" in techniques or any(
        t in techniques for t in ("EP", "BVA", "DT")
    )
