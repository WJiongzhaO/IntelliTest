"""Prompt loader for requirement structuring (FR 1.1).

Loads the canonical prompt template from the version-controlled file at
prompts/requirement_structure.json — the single source of truth.

Each prompt contains the three required parts:
  - System Prompt
  - User Prompt Template (with {requirement_text} placeholder)
  - Output Schema
"""

import json
from pathlib import Path

# Canonical prompt file — version-controlled, independent of code
PROMPT_FILE = Path(__file__).resolve().parents[4] / "prompts" / "requirement_structure.json"

with open(PROMPT_FILE, encoding="utf-8") as fh:
    _data = json.load(fh)

SYSTEM_PROMPT: str = _data["system_prompt"]
OUTPUT_SCHEMA_DESCRIPTION: str = _data["output_schema"]
USER_PROMPT_TEMPLATE: str = _data["user_prompt_template"]
FEW_SHOT_EXAMPLES: list[dict] = _data["few_shot_examples"]
