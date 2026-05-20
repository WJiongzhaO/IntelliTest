"""Core data models: TestCase, TestSuite, and related entities."""

from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class BlackBoxTechnique(str, Enum):
    """ISO 29119-4 black-box testing techniques."""
    EP = "EP"  # Equivalence Partitioning
    BVA = "BVA"  # Boundary Value Analysis
    DT = "DT"  # Decision Table


class CoverageItem(BaseModel):
    """Represents a coverage item for test design traceability."""
    
    id: str = Field(description="Unique coverage item identifier")
    requirement_id: str = Field(description="Source requirement reference")
    description: str = Field(description="Description of what needs to be covered")
    item_type: str = Field(
        description="Type: input_field, boundary, condition, decision_rule, etc."
    )
    selected_techniques: list[BlackBoxTechnique] = Field(
        default_factory=list,
        description="Selected testing techniques for this coverage item"
    )
    covered_by_test_cases: list[str] = Field(
        default_factory=list,
        description="Test case IDs that cover this item"
    )


class TestCase(BaseModel):
    """A single test case conforming to ISO 29119-4 / ISTQB structure."""

    id: str = Field(description="Unique test case identifier")
    requirement_id: str = Field(description="Source requirement reference")
    title: str = Field(description="Brief test case title")
    precondition: Optional[str] = Field(default=None, description="Preconditions")
    test_steps: list[str] = Field(default_factory=list, description="Ordered test steps")
    test_data: Optional[str] = Field(default=None, description="Specific test data / inputs")
    expected_result: Optional[str] = Field(default=None, description="Expected outcome")
    technique: Optional[Union[BlackBoxTechnique, Literal["StateTransition"]]] = Field(
        default=None, description="Source technique (EP / BVA / DT / StateTransition)"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Risk-based priority")
    risk_score: Optional[int] = Field(default=None, ge=1, le=25, description="Risk score 1-25")
    coverage_items: list[str] = Field(
        default_factory=list, description="Coverage item IDs exercised by this test case"
    )
    modified_by_user: bool = Field(default=False, description="Whether human has edited this")


class TestSuite(BaseModel):
    """A collection of test cases, with metadata."""

    id: str = Field(description="Unique suite identifier")
    name: str = Field(description="Suite name")
    description: Optional[str] = Field(default=None)
    test_cases: list[TestCase] = Field(default_factory=list)
    created_at: Optional[str] = None
    optimization_applied: Optional[str] = Field(default=None)
