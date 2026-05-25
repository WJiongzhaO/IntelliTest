"""Requirement data models."""

from typing import Optional

from pydantic import BaseModel, Field


class StructuredRequirement(BaseModel):
    """LLM-parsed structured representation of a natural-language requirement."""

    id: str = Field(description="Unique requirement identifier")
    title: Optional[str] = Field(default=None, description="Human-readable requirement title")
    raw_text: str = Field(description="Original requirement text")
    input_fields: list[str] = Field(default_factory=list, description="Identified input fields")
    data_ranges: list[str] = Field(default_factory=list, description="Data ranges / constraints")
    conditions: list[str] = Field(default_factory=list, description="Trigger conditions")
    expected_actions: list[str] = Field(
        default_factory=list, description="Expected system actions"
    )
    risk_score: Optional[int] = Field(default=None, ge=1, le=25)
    priority: Optional[str] = Field(default=None)
