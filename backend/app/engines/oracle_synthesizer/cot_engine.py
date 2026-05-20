"""Chain-of-Thought oracle synthesis via LLM."""

from __future__ import annotations

import json

from app.exceptions import IntelliTestError, OracleSynthesisError
from app.models.requirement import StructuredRequirement
from app.models.test_case import TestCase
from app.prompts.loader import load_prompt_template, render_user_prompt
from app.services.llm_types import LLMClientProtocol
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CotOraclePayload:
    """Parsed CoT LLM response."""

    def __init__(
        self,
        reasoning_steps: list[str],
        expected_result: str,
        confidence: float | None = None,
    ) -> None:
        self.reasoning_steps = reasoning_steps
        self.expected_result = expected_result
        self.confidence = confidence


def synthesize_cot(
    requirement: StructuredRequirement,
    test_case: TestCase,
    llm: LLMClientProtocol | None = None,
) -> CotOraclePayload:
    """Run CoT prompt and parse structured oracle fields."""
    if llm is None:
        from app.services.llm_client import LLMClient

        client = LLMClient()
    else:
        client = llm
    template = load_prompt_template("oracle_synthesis")
    user_prompt = render_user_prompt(
        template,
        raw_text=requirement.raw_text,
        expected_actions=json.dumps(requirement.expected_actions, ensure_ascii=False),
        precondition=test_case.precondition or "",
        test_steps=json.dumps(test_case.test_steps, ensure_ascii=False),
        test_data=test_case.test_data or "",
    )

    try:
        payload = client.complete_json(
            template["system"],
            user_prompt,
            temperature=0.0,
        )
    except IntelliTestError as exc:
        raise OracleSynthesisError(f"Oracle LLM failed: {exc}") from exc

    try:
        steps = [str(item) for item in payload["reasoning_steps"]]
        expected = str(payload["expected_result"])
        confidence = payload.get("confidence")
        if confidence is not None:
            confidence = float(confidence)
    except (KeyError, TypeError, ValueError) as exc:
        raise OracleSynthesisError(f"Invalid oracle JSON: {exc}") from exc

    logger.info(
        "CoT oracle synthesized steps=%d result_len=%d",
        len(steps),
        len(expected),
    )
    return CotOraclePayload(steps, expected, confidence)
