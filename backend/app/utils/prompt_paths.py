"""Resolve shared prompts/ directory for local dev and Docker (/app/prompts mount)."""

from pathlib import Path


def resolve_prompt_file(filename: str, *, from_file: str | Path) -> Path:
    """Return path to a file under prompts/ (repo root or backend-relative)."""
    here = Path(from_file).resolve()
    candidates = (
        here.parents[4] / "prompts" / filename,
        here.parents[3] / "prompts" / filename,
        here.parents[2] / "prompts" / filename,
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"Prompt file not found: {filename} (searched: {', '.join(str(c) for c in candidates)})"
    )


def resolve_prompts_dir(*, from_file: str | Path) -> Path:
    """Return the prompts directory if it exists."""
    here = Path(from_file).resolve()
    for base in (here.parents[4], here.parents[3], here.parents[2]):
        directory = base / "prompts"
        if directory.is_dir():
            return directory
    return here.parents[3] / "prompts"
