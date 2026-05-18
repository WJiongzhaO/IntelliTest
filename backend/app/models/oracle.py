"""Test oracle models for CoT synthesis and review (FR 5.0)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

OracleStatus = Literal["pending_review", "confirmed", "rejected"]


class OracleResult(BaseModel):
    """Synthesized or validated expected result with Chain-of-Thought trace."""

    id: str = Field(description="Unique oracle record identifier")
    test_case_id: str = Field(description="Associated test case identifier")
    expected_result: str = Field(description="Synthesized or confirmed expected outcome")
    reasoning_steps: list[str] = Field(
        default_factory=list, description="CoT reasoning steps for UI review"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Optional model confidence 0-1"
    )
    consistent_with_requirement: bool = Field(
        description="Whether expected_result aligns with requirement expected_actions"
    )
    validation_messages: list[str] = Field(
        default_factory=list, description="Consistency or rule validation messages"
    )
    status: OracleStatus = Field(
        default="pending_review",
        description="Review lifecycle status",
    )
    modified_by_user: bool = Field(
        default=False, description="Whether a human confirmed or edited this oracle"
    )
    revision: int = Field(default=0, ge=0, description="Revision for human review workflow")
