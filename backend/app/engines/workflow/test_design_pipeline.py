"""Combined blackbox + whitebox + oracle test design pipeline."""

from __future__ import annotations

import uuid
from typing import Sequence

from app.engines.oracle_synthesizer.synthesizer import DefaultOracleSynthesizer
from app.engines.whitebox_modeler.generator import DefaultStateModelGenerator
from app.models.requirement import StructuredRequirement
from app.models.state_machine import CoverageCriterion
from app.models.test_case import Priority, TestCase, TestSuite
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_PRIORITY_RANK = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
_TECHNIQUE_BLACKBOX = {"EP", "BVA", "DT"}


def run_combined_pipeline(
    requirement: StructuredRequirement,
    *,
    techniques: Sequence[str],
    coverage: CoverageCriterion = CoverageCriterion.ALL_TRANSITIONS,
    synthesize_oracles: bool = True,
    blackbox_cases: list[TestCase] | None = None,
    use_llm: bool = True,
) -> TestSuite:
    """Merge blackbox and whitebox cases, optionally synthesize oracles."""
    merged: dict[str, TestCase] = {}

    if blackbox_cases:
        for case in blackbox_cases:
            if case.technique in _TECHNIQUE_BLACKBOX:
                _upsert_case(merged, case)

    if "StateTransition" in techniques:
        generator = DefaultStateModelGenerator()
        _, _, state_cases = generator.generate(
            requirement,
            coverage=coverage,
            use_llm=use_llm,
        )
        for case in state_cases:
            _upsert_case(merged, case)

    cases = list(merged.values())

    if synthesize_oracles:
        synthesizer = DefaultOracleSynthesizer()
        for index, case in enumerate(cases):
            if case.expected_result:
                continue
            oracle = synthesizer.synthesize(requirement, case, use_llm=use_llm)
            cases[index] = case.model_copy(update={"expected_result": oracle.expected_result})

    suite = TestSuite(
        id=f"suite-{uuid.uuid4().hex[:8]}",
        name=f"Combined design for {requirement.id}",
        description=f"Techniques: {', '.join(techniques)}",
        test_cases=cases,
    )
    logger.info(
        "Combined pipeline suite=%s cases=%d techniques=%s",
        suite.id,
        len(cases),
        list(techniques),
    )
    return suite


def _upsert_case(store: dict[str, TestCase], case: TestCase) -> None:
    key = "|".join(sorted(case.coverage_items)) or case.id
    existing = store.get(key)
    if existing is None or _priority_rank(case) > _priority_rank(existing):
        store[key] = case


def _priority_rank(case: TestCase) -> int:
    return _PRIORITY_RANK.get(case.priority, 0)
