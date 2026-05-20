"""Prompt loader for FR 2.0 risk analysis."""

import json

from app.utils.prompt_paths import resolve_prompt_file

PROMPT_FILE = resolve_prompt_file("risk_analysis.json", from_file=__file__)

with open(PROMPT_FILE, encoding="utf-8") as fh:
    _data = json.load(fh)

SYSTEM_PROMPT: str = _data["system_prompt"]
OUTPUT_SCHEMA_DESCRIPTION: str = _data["output_schema"]
USER_PROMPT_TEMPLATE: str = _data["user_prompt_template"]
FEW_SHOT_EXAMPLES: list[dict] = _data["few_shot_examples"]
