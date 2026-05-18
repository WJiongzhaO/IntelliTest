"""Validate LLM JSON for risk dimensions."""

import json
import re


class RiskValidationError(ValueError):
    """Raised when LLM risk output fails validation."""


def extract_json(text: str) -> str:
    """Extract JSON object from LLM text."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        return fence_match.group(1).strip()
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        return text[brace_start : brace_end + 1]
    return text


def validate_risk_output(data: dict) -> None:
    """Ensure impact/likelihood and rationales exist."""
    required = {"impact", "likelihood", "impact_rationale", "likelihood_rationale"}
    missing = required - set(data.keys())
    if missing:
        raise RiskValidationError(f"Missing keys: {missing}")

    for key in ("impact", "likelihood"):
        v = data[key]
        if not isinstance(v, int) or not (1 <= v <= 5):
            raise RiskValidationError(f"'{key}' must be integer 1–5, got {v!r}")

    for key in ("impact_rationale", "likelihood_rationale"):
        if not isinstance(data[key], str):
            raise RiskValidationError(f"'{key}' must be a string")


def parse_and_validate(llm_response: str) -> dict:
    """Parse JSON from LLM response and validate."""
    json_str = extract_json(llm_response)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise RiskValidationError(f"Invalid JSON: {exc}") from exc
    validate_risk_output(data)
    return data
