"""FR 2.0 — Risk analysis engine."""

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.engines.risk_analyzer.llm_client import call_llm_risk
from app.engines.risk_analyzer.schema import RiskValidationError, parse_and_validate
from app.models.risk import RiskAssessment
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskAnalysisError(RuntimeError):
    """Raised when risk analysis fails after retries."""


def priority_from_score(risk_score: int) -> str:
    """Map 1–25 product score to High / Medium / Low (assignment brief).

    Args:
        risk_score: impact × likelihood.

    Returns:
        Priority label string.
    """
    if risk_score >= 15:
        return "High"
    if risk_score >= 8:
        return "Medium"
    return "Low"


def score_from_dimensions(impact: int, likelihood: int) -> int:
    """Compute risk score as Impact × Likelihood (1–25)."""
    return int(impact * likelihood)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def _call_and_validate_risk(
    requirement_id: str,
    raw_text: str,
    structured_json: str,
) -> dict:
    response_text = await call_llm_risk(requirement_id, raw_text, structured_json)
    return parse_and_validate(response_text)


async def analyze_requirement_risk(
    requirement_id: str,
    raw_text: str,
    *,
    input_fields: list[str] | None = None,
    data_ranges: list[str] | None = None,
    conditions: list[str] | None = None,
    expected_actions: list[str] | None = None,
) -> RiskAssessment:
    """Run LLM risk dimensions, then compute score and priority.

    Args:
        requirement_id: Requirement primary key.
        raw_text: Original requirement narrative.
        input_fields: Structured inputs from FR 1.1 (optional).
        data_ranges: Structured ranges from FR 1.1 (optional).
        conditions: Structured conditions from FR 1.1 (optional).
        expected_actions: Structured actions from FR 1.1 (optional).

    Returns:
        RiskAssessment ready for persistence.

    Raises:
        RiskAnalysisError: If LLM output stays invalid after retries.
    """
    payload = {
        "input_fields": input_fields or [],
        "data_ranges": data_ranges or [],
        "conditions": conditions or [],
        "expected_actions": expected_actions or [],
    }
    import json

    structured_json = json.dumps(payload, ensure_ascii=False)

    logger.info("Risk analysis start for %s", requirement_id)
    try:
        data = await _call_and_validate_risk(requirement_id, raw_text, structured_json)
    except (RiskValidationError, Exception) as exc:
        logger.error("Risk analysis failed for %s: %s", requirement_id, exc)
        raise RiskAnalysisError(
            f"Risk analysis failed for {requirement_id} after "
            f"{settings.llm_max_retries} retries: {exc}"
        ) from exc

    impact = data["impact"]
    likelihood = data["likelihood"]
    rs = score_from_dimensions(impact, likelihood)
    priority = priority_from_score(rs)

    assessment = RiskAssessment(
        requirement_id=requirement_id,
        impact=impact,
        likelihood=likelihood,
        risk_score=rs,
        priority=priority,
        impact_rationale=data.get("impact_rationale", ""),
        likelihood_rationale=data.get("likelihood_rationale", ""),
    )
    logger.info(
        "Risk analysis done %s: score=%s priority=%s",
        requirement_id,
        rs,
        priority,
    )
    return assessment
