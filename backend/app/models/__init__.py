"""Shared data models for the entire application."""

from app.models.oracle import OracleResult, OracleStatus
from app.models.requirement import StructuredRequirement
from app.models.state_machine import (
    CoverageCriterion,
    StateMachineModel,
    StateTransitionTuple,
    TestSequence,
)
from app.models.test_case import (
    BlackBoxTechnique,
    CoverageItem,
    Priority,
    TestCase,
    TestSuite,
)

__all__ = [
    "BlackBoxTechnique",
    "CoverageCriterion",
    "CoverageItem",
    "OracleResult",
    "OracleStatus",
    "Priority",
    "StateMachineModel",
    "StateTransitionTuple",
    "StructuredRequirement",
    "TestCase",
    "TestSequence",
    "TestSuite",
]
