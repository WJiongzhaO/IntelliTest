"""FR 1.1 — Requirement Structuring Engine.

Orchestrates:
  1. LLM call for semantic parsing
  2. JSON extraction and schema validation
  3. Retry on failure (up to 3 attempts)
"""

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.engines.requirement_structurer.llm_client import call_llm
from app.engines.requirement_structurer.schema import ValidationError, parse_and_validate
from app.models.requirement import StructuredRequirement
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class StructuringError(RuntimeError):
    """Raised when requirement structuring fails after all retries."""


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def _call_and_validate(requirement_text: str) -> dict:
    """Single attempt: call LLM, parse, validate."""
    response_text = await call_llm(requirement_text)
    data = parse_and_validate(response_text)
    return data


async def structure_requirement(
    requirement_id: str,
    raw_text: str,
    title: str | None = None,
) -> StructuredRequirement:
    """Parse a single requirement's raw text into structured components.

    Args:
        requirement_id: The requirement's unique ID.
        raw_text: The natural-language requirement text.

    Returns:
        A StructuredRequirement with parsed fields.

    Raises:
        StructuringError: If LLM fails to produce valid output after all retries.
    """
    logger.info("Structuring requirement %s (%d chars)", requirement_id, len(raw_text))

    try:
        data = await _call_and_validate(raw_text)
    except (ValidationError, Exception) as exc:
        logger.error("Structuring failed for %s: %s", requirement_id, exc)
        raise StructuringError(
            f"Failed to structure requirement {requirement_id} after "
            f"{settings.llm_max_retries} retries: {exc}"
        ) from exc

    structured = StructuredRequirement(
        id=requirement_id,
        title=title,
        raw_text=raw_text,
        input_fields=data["input_fields"],
        data_ranges=data["data_ranges"],
        conditions=data["conditions"],
        expected_actions=data["expected_actions"],
    )

    logger.info(
        "Structured requirement %s: %d fields, %d ranges, %d conditions, %d actions",
        requirement_id,
        len(structured.input_fields),
        len(structured.data_ranges),
        len(structured.conditions),
        len(structured.expected_actions),
    )
    return structured
