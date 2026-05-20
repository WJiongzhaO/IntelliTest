"""Load versioned prompt templates from the repository prompts/ directory."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict

from app.exceptions import IntelliTestError


class PromptTemplate(TypedDict):
    system: str
    user: str
    output_schema: str
    few_shot: str


_SECTION_PATTERN = re.compile(r"^===(SYSTEM|USER|OUTPUT_SCHEMA|FEW_SHOT)===$", re.MULTILINE)


def prompts_dir() -> Path:
    """Return the shared prompts directory (repo root or Docker /app/prompts)."""
    from app.utils.prompt_paths import resolve_prompts_dir

    return resolve_prompts_dir(from_file=__file__)


def load_prompt_template(name: str) -> PromptTemplate:
    """Load a prompt file by basename (without .txt)."""
    path = prompts_dir() / f"{name}.txt"
    if not path.is_file():
        raise IntelliTestError(f"Prompt template not found: {path}")

    raw = path.read_text(encoding="utf-8")
    sections: dict[str, list[str]] = {
        "system": [],
        "user": [],
        "output_schema": [],
        "few_shot": [],
    }
    current: str | None = None

    for line in raw.splitlines():
        match = _SECTION_PATTERN.match(line.strip())
        if match:
            current = match.group(1).lower()
            continue
        if current:
            key = "output_schema" if current == "output_schema" else current
            sections[key].append(line)

    return PromptTemplate(
        system="\n".join(sections["system"]).strip(),
        user="\n".join(sections["user"]).strip(),
        output_schema="\n".join(sections["output_schema"]).strip(),
        few_shot="\n".join(sections["few_shot"]).strip(),
    )


def render_user_prompt(template: PromptTemplate, **placeholders: str) -> str:
    """Replace {{key}} placeholders in the user section."""
    text = template["user"]
    if template["few_shot"]:
        text = f"{text}\n\nFew-shot reference:\n{template['few_shot']}"
    for key, value in placeholders.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    schema = template["output_schema"]
    if schema:
        text = f"{text}\n\nOutput Schema:\n{schema}"
    return text
