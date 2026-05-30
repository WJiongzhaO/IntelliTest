"""Black-box test case generation module implementing ISO 29119-4 techniques.

This module provides:
- Equivalence Partitioning (EP) generator
- Boundary Value Analysis (BVA) generator
- Decision Table (DT) generator
- Coverage item management
- Unified generation engine
"""

from app.engines.blackbox_generator.base import BaseBlackBoxGenerator
from app.engines.blackbox_generator.boundary_value_analysis import BoundaryValueAnalysisGenerator
from app.engines.blackbox_generator.coverage_manager import CoverageManager
from app.engines.blackbox_generator.decision_table import DecisionTableGenerator
from app.engines.blackbox_generator.engine import BlackBoxTestGenerator
from app.engines.blackbox_generator.equivalence_partitioning import EquivalencePartitioningGenerator
from app.engines.blackbox_generator.llm_generator import LLMBlackBoxGenerator

__all__ = [
    'BaseBlackBoxGenerator',
    'EquivalencePartitioningGenerator',
    'BoundaryValueAnalysisGenerator',
    'DecisionTableGenerator',
    'CoverageManager',
    'BlackBoxTestGenerator',
    'LLMBlackBoxGenerator',
]
