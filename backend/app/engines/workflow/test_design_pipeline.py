"""Combined blackbox + whitebox + oracle test design pipeline."""

from __future__ import annotations

import uuid
from typing import Sequence

from app.engines.blackbox_generator import BlackBoxTestGenerator
from app.engines.oracle_synthesizer.synthesizer import DefaultOracleSynthesizer
from app.engines.whitebox_modeler.generator import DefaultStateModelGenerator
from app.exceptions import WhiteboxModelError
from app.models.requirement import StructuredRequirement
from app.models.state_machine import CoverageCriterion
from app.models.test_case import BlackBoxTechnique, Priority, TestCase, TestSuite
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_PRIORITY_RANK = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
_BLACKBOX_CODES = frozenset({"EP", "BVA", "DT"})


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

    for case in blackbox_cases or []:
        if _is_blackbox_technique(case):
            _upsert_case(merged, case)

    requested_blackbox = [t for t in techniques if t in _BLACKBOX_CODES]
    if requested_blackbox:
        engine = BlackBoxTestGenerator()
        generated = _generate_blackbox_cases(engine, requirement, requested_blackbox)
        for case in generated:
            _upsert_case(merged, case)

    if "StateTransition" in techniques:
        generator = DefaultStateModelGenerator()
        try:
            _, _, state_cases = generator.generate(
                requirement,
                coverage=coverage,
                use_llm=use_llm,
            )
        except WhiteboxModelError as exc:
            if not use_llm:
                raise
            logger.warning(
                "LLM state model failed, falling back to rule-based model: %s",
                exc,
            )
            _, _, state_cases = generator.generate(
                requirement,
                coverage=coverage,
                use_llm=False,
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
    from app.repositories.memory_store import store

    store.last_suite_id = suite.id
    for case in cases:
        store.test_cases[case.id] = case
    logger.info(
        "Combined pipeline suite=%s cases=%d techniques=%s",
        suite.id,
        len(cases),
        list(techniques),
    )
    return suite


def _generate_blackbox_cases(
    engine: BlackBoxTestGenerator,
    requirement: StructuredRequirement,
    techniques: list[str],
) -> list[TestCase]:
    if set(techniques) >= _BLACKBOX_CODES:
        return engine.generate_all_techniques(requirement)

    cases: list[TestCase] = []
    for code in techniques:
        technique = BlackBoxTechnique(code)
        cases.extend(engine.generate_specific_technique(requirement, technique))
    return cases


def _technique_code(case: TestCase) -> str | None:
    if case.technique is None:
        return None
    if isinstance(case.technique, BlackBoxTechnique):
        return case.technique.value
    return str(case.technique)


def _is_blackbox_technique(case: TestCase) -> bool:
    code = _technique_code(case)
    return code in _BLACKBOX_CODES if code else False


def _upsert_case(store: dict[str, TestCase], case: TestCase) -> None:
    key = "|".join(sorted(case.coverage_items)) or case.id
    existing = store.get(key)
    if existing is None or _priority_rank(case) > _priority_rank(existing):
        store[key] = case


def _priority_rank(case: TestCase) -> int:
    return _PRIORITY_RANK.get(case.priority, 0)
