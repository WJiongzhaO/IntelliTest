"""JSON Schema for validating LLM-structured requirement output."""

import json
import re

OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "required": ["input_fields", "data_ranges", "conditions", "expected_actions"],
    "properties": {
        "input_fields": {
            "type": "array",
            "items": {"type": "string"},
        },
        "data_ranges": {
            "type": "array",
            "items": {"type": "string"},
        },
        "conditions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "expected_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


class ValidationError(ValueError):
    """Raised when LLM output fails schema validation."""


def extract_json(text: str) -> str:
    """Extract JSON object from text that may contain markdown fences or extra content."""
    text = text.strip()
    # Try to find JSON within markdown code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        return fence_match.group(1).strip()
    # Try to find first { ... } block
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        return text[brace_start : brace_end + 1]
    return text


def validate_structured_output(data: dict) -> None:
    """Validate that `data` conforms to the expected output schema.

    Checks for required keys, correct types, and non-empty content.
    """
    required_keys = {"input_fields", "data_ranges", "conditions", "expected_actions"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValidationError(f"Missing required keys: {missing}")

    for key in required_keys:
        if not isinstance(data[key], list):
            raise ValidationError(f"'{key}' must be an array, got {type(data[key]).__name__}")
        for item in data[key]:
            if not isinstance(item, str):
                raise ValidationError(f"'{key}' contains non-string item: {item!r}")

    total_items = sum(len(data[k]) for k in required_keys)
    if total_items == 0:
        raise ValidationError("All four output fields are empty — LLM produced no content")


def parse_and_validate(llm_response: str) -> dict:
    """Extract JSON from LLM response and validate against schema."""
    json_str = extract_json(llm_response)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON from LLM: {exc}") from exc

    validate_structured_output(data)
    return data
