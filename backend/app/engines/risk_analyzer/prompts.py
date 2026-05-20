"""Prompt loader for FR 2.0 risk analysis."""

import json
from pathlib import Path


def _resolve_prompt_file(filename: str) -> Path:
    """Resolve prompts directory: repo root (local dev) or backend-relative (Docker volume)."""
    here = Path(__file__).resolve()
    repo_candidate = here.parents[4] / "prompts" / filename
    if repo_candidate.is_file():
        return repo_candidate
    return here.parents[3] / "prompts" / filename


PROMPT_FILE = _resolve_prompt_file("risk_analysis.json")

with open(PROMPT_FILE, encoding="utf-8") as fh:
    _data = json.load(fh)

SYSTEM_PROMPT: str = _data["system_prompt"]
OUTPUT_SCHEMA_DESCRIPTION: str = _data["output_schema"]
USER_PROMPT_TEMPLATE: str = _data["user_prompt_template"]
FEW_SHOT_EXAMPLES: list[dict] = _data["few_shot_examples"]
