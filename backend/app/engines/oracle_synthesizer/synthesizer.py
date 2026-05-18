"""Oracle synthesizer: CoT + consistency validation."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.engines.oracle_synthesizer.consistency_checker import validate_oracle
from app.engines.oracle_synthesizer.cot_engine import synthesize_cot
from app.exceptions import OracleSynthesisError
from app.models.oracle import OracleResult
from app.models.requirement import StructuredRequirement
from app.models.test_case import TestCase
from app.services.llm_types import LLMClientProtocol
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class OracleSynthesizer(Protocol):
    """Generate or validate test oracles for test cases."""

    def synthesize(
        self,
        requirement: StructuredRequirement,
        test_case: TestCase,
        *,
        use_llm: bool = True,
    ) -> OracleResult:
        ...

    def validate_only(
        self,
        requirement: StructuredRequirement,
        test_case: TestCase,
        expected_result: str,
    ) -> OracleResult:
        ...


class DefaultOracleSynthesizer:
    """Default FR 5.0 oracle synthesizer."""

    def __init__(self, llm: LLMClientProtocol | None = None) -> None:
        self._llm = llm

    def synthesize(
        self,
        requirement: StructuredRequirement,
        test_case: TestCase,
        *,
        use_llm: bool = True,
    ) -> OracleResult:
        if use_llm:
            payload = synthesize_cot(requirement, test_case, self._llm)
            expected = payload.expected_result
            steps = payload.reasoning_steps
            confidence = payload.confidence
        else:
            expected = _rule_based_expected(requirement, test_case)
            steps = [
                "Apply requirement expected_actions to test steps.",
                f"Conclude: {expected}",
            ]
            confidence = 0.5

        consistent, messages = validate_oracle(requirement, test_case, expected)
        status = "pending_review" if consistent else "pending_review"

        result = OracleResult(
            id=f"oracle-{uuid.uuid4().hex[:8]}",
            test_case_id=test_case.id,
            expected_result=expected,
            reasoning_steps=steps,
            confidence=confidence,
            consistent_with_requirement=consistent,
            validation_messages=messages,
            status=status,
        )
        logger.info(
            "Oracle synthesized case=%s consistent=%s messages=%d",
            test_case.id,
            consistent,
            len(messages),
        )
        return result

    def validate_only(
        self,
        requirement: StructuredRequirement,
        test_case: TestCase,
        expected_result: str,
    ) -> OracleResult:
        consistent, messages = validate_oracle(requirement, test_case, expected_result)
        return OracleResult(
            id=f"oracle-{uuid.uuid4().hex[:8]}",
            test_case_id=test_case.id,
            expected_result=expected_result,
            reasoning_steps=[],
            confidence=None,
            consistent_with_requirement=consistent,
            validation_messages=messages,
            status="pending_review",
        )


def _rule_based_expected(
    requirement: StructuredRequirement,
    test_case: TestCase,
) -> str:
    if requirement.expected_actions:
        return requirement.expected_actions[0]
    if test_case.test_steps:
        return f"System completes: {test_case.test_steps[-1]}"
    return "System behaves as specified in the requirement."


OracleSynthesizer = DefaultOracleSynthesizer
