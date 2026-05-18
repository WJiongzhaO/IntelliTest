"""Risk assessment models (FR 2.0)."""

from typing import Optional

from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    """Per-requirement risk output persisted and returned by APIs."""

    requirement_id: str = Field(description="Requirement identifier")
    impact: int = Field(ge=1, le=5, description="Impact rating 1–5")
    likelihood: int = Field(ge=1, le=5, description="Likelihood rating 1–5")
    risk_score: int = Field(ge=1, le=25, description="Impact × Likelihood")
    priority: str = Field(description='Mapped priority: "High" | "Medium" | "Low"')
    impact_rationale: str = Field(default="", description="Brief rationale for impact")
    likelihood_rationale: str = Field(default="", description="Brief rationale for likelihood")


class RiskDashboardSummary(BaseModel):
    """Aggregated figures for dashboard consumption."""

    total_requirements: int = Field(ge=0)
    analyzed_count: int = Field(ge=0, description="Requirements with completed risk analysis")
    priority_high: int = Field(ge=0)
    priority_medium: int = Field(ge=0)
    priority_low: int = Field(ge=0)
    average_risk_score: Optional[float] = Field(
        default=None, description="Mean risk_score over analyzed requirements"
    )
    highest_risk: list[RiskAssessment] = Field(
        default_factory=list,
        description="Top N highest risk requirements (full assessment)",
    )
