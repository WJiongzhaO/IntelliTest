"""Resolve shared prompts/ directory for local dev and Docker (/app/prompts mount)."""

from pathlib import Path


_PROMPT_MARKERS = (
    "state_transition.txt",
    "oracle_synthesis.txt",
    "requirement_structure.json",
    "risk_analysis.json",
)


def _candidate_prompt_dirs(here: Path) -> list[Path]:
    """Return prompt directory candidates without assuming a fixed depth."""

    candidates: list[Path] = []
    for base in (here.parent, *here.parents):
        candidates.append(base / "prompts")
        candidates.append(base / "backend" / "prompts")

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate not in seen:
            unique.append(candidate)
            seen.add(candidate)
    return unique


def _is_shared_prompts_dir(path: Path) -> bool:
    """Avoid selecting backend/app/prompts, which only stores loader code."""

    return path.is_dir() and any((path / marker).is_file() for marker in _PROMPT_MARKERS)


def resolve_prompt_file(filename: str, *, from_file: str | Path) -> Path:
    """Return path to a file under prompts/ (repo root or backend-relative)."""
    here = Path(from_file).resolve()
    candidates = [directory / filename for directory in _candidate_prompt_dirs(here)]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"Prompt file not found: {filename} (searched: {', '.join(str(c) for c in candidates)})"
    )


def resolve_prompts_dir(*, from_file: str | Path) -> Path:
    """Return the prompts directory if it exists."""
    here = Path(from_file).resolve()
    candidates = _candidate_prompt_dirs(here)
    for directory in candidates:
        if _is_shared_prompts_dir(directory):
            return directory
    raise FileNotFoundError(
        f"Prompts directory not found (searched: {', '.join(str(c) for c in candidates)})"
    )
