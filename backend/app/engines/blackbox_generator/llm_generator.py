"""LLM-driven black-box test design (ISO 29119-4 EP, BVA, DT)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.exceptions import BlackboxGenerationError, IntelliTestError
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, CoverageItem, TestCase
from app.prompts.loader import load_prompt_template, render_user_prompt
from app.services.llm_types import LLMClientProtocol
from app.utils.logger import setup_logger

from app.engines.blackbox_generator.schema import (
    parse_coverage_items,
    parse_test_cases,
    validate_blackbox_payload,
)

logger = setup_logger(__name__)

_DEFAULT_TECHNIQUES = list(BlackBoxTechnique)


@dataclass
class BlackboxLLMResult:
    """Full LLM black-box design output."""

    test_cases: list[TestCase]
    coverage_items: list[CoverageItem]
    analysis: dict[str, Any]


class LLMBlackBoxGenerator:
    """Generate EP / BVA / DT test cases via structured LLM prompts."""

    PROMPT_NAME = "blackbox_test_design"

    def __init__(self, llm: LLMClientProtocol | None = None) -> None:
        self._llm = llm

    @property
    def llm(self) -> LLMClientProtocol:
        if self._llm is None:
            from app.services.llm_client import LLMClient

            return LLMClient()
        return self._llm

    def generate(
        self,
        requirement: StructuredRequirement,
        *,
        techniques: list[BlackBoxTechnique] | None = None,
    ) -> BlackboxLLMResult:
        """Run LLM test design with validation and one repair retry."""
        requested = techniques or _DEFAULT_TECHNIQUES
        template = load_prompt_template(self.PROMPT_NAME)
        user_prompt = self._build_user_prompt(template, requirement, requested)

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                payload = self.llm.complete_json(
                    template["system"],
                    user_prompt if attempt == 0 else self._repair_prompt(user_prompt, last_error),
                    temperature=0.0,
                )
                validate_blackbox_payload(payload, requested_techniques=requested)
                test_cases = parse_test_cases(
                    payload, requirement, requested_techniques=requested
                )
                coverage_items = parse_coverage_items(payload, requirement)
                analysis = payload.get("analysis") or {}
                logger.info(
                    "LLM blackbox generated req=%s cases=%d techniques=%s attempt=%d",
                    requirement.id,
                    len(test_cases),
                    [t.value for t in requested],
                    attempt + 1,
                )
                return BlackboxLLMResult(
                    test_cases=test_cases,
                    coverage_items=coverage_items,
                    analysis=analysis if isinstance(analysis, dict) else {},
                )
            except Exception as exc:
                if not isinstance(exc, (IntelliTestError, BlackboxGenerationError)):
                    exc = BlackboxGenerationError(str(exc))
                last_error = exc
                logger.warning(
                    "LLM blackbox attempt %d failed for req=%s: %s",
                    attempt + 1,
                    requirement.id,
                    exc,
                )

        raise BlackboxGenerationError(
            f"LLM black-box generation failed after retries: {last_error}"
        ) from last_error

    def generate_test_cases(
        self,
        requirement: StructuredRequirement,
        *,
        techniques: list[BlackBoxTechnique] | None = None,
    ) -> list[TestCase]:
        """Convenience wrapper returning only test cases."""
        return self.generate(requirement, techniques=techniques).test_cases

    def _build_user_prompt(
        self,
        template: dict[str, str],
        requirement: StructuredRequirement,
        techniques: list[BlackBoxTechnique],
    ) -> str:
        return render_user_prompt(
            template,
            requirement_id=requirement.id,
            title=requirement.title or "",
            raw_text=requirement.raw_text,
            input_fields=json.dumps(requirement.input_fields, ensure_ascii=False),
            data_ranges=json.dumps(requirement.data_ranges, ensure_ascii=False),
            conditions=json.dumps(requirement.conditions, ensure_ascii=False),
            expected_actions=json.dumps(requirement.expected_actions, ensure_ascii=False),
            priority=requirement.priority or "Medium",
            risk_score=str(requirement.risk_score or ""),
            techniques=", ".join(t.value for t in techniques),
        )

    @staticmethod
    def _repair_prompt(original: str, error: Exception | None) -> str:
        detail = str(error) if error else "unknown validation error"
        return (
            f"{original}\n\n"
            "Your previous response failed validation. Fix the JSON and respond again.\n"
            f"Validation error: {detail}\n"
            "Ensure every requested technique has at least one test case "
            "(BVA may be skipped only if bva_applicable is false with bva_skip_reason)."
        )
