"""Main black-box test generation engine.

Orchestrates ISO 29119-4 techniques (EP, BVA, DT) via LLM-first design
with rule-based fallback when LLM is disabled or fails.
"""

from typing import Optional

from app.engines.blackbox_generator.boundary_value_analysis import BoundaryValueAnalysisGenerator
from app.engines.blackbox_generator.coverage_manager import CoverageManager
from app.engines.blackbox_generator.decision_table import DecisionTableGenerator
from app.engines.blackbox_generator.equivalence_partitioning import EquivalencePartitioningGenerator
from app.engines.blackbox_generator.llm_generator import LLMBlackBoxGenerator
from app.exceptions import BlackboxGenerationError
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, TestCase
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BlackBoxTestGenerator:
    """Main orchestrator for black-box test case generation."""

    def __init__(self, use_llm: bool = True):
        """Initialize generators. LLM is the default path when use_llm=True."""
        self.use_llm = use_llm
        self.llm_generator = LLMBlackBoxGenerator()
        self.ep_generator = EquivalencePartitioningGenerator()
        self.bva_generator = BoundaryValueAnalysisGenerator()
        self.dt_generator = DecisionTableGenerator()
        self.coverage_manager = CoverageManager()

        self.generators = {
            BlackBoxTechnique.EP: self.ep_generator,
            BlackBoxTechnique.BVA: self.bva_generator,
            BlackBoxTechnique.DT: self.dt_generator,
        }

    def generate_all_techniques(
        self,
        requirement: StructuredRequirement,
        *,
        use_llm: bool | None = None,
    ) -> list[TestCase]:
        """Generate test cases using all three black-box techniques."""
        return self._generate(
            requirement,
            list(BlackBoxTechnique),
            use_llm=use_llm,
        )

    def generate_specific_technique(
        self,
        requirement: StructuredRequirement,
        technique: BlackBoxTechnique,
        *,
        use_llm: bool | None = None,
    ) -> list[TestCase]:
        """Generate test cases using a specific technique."""
        return self._generate(requirement, [technique], use_llm=use_llm)

    def generate_with_coverage_tracking(
        self,
        requirement: StructuredRequirement,
        selected_techniques: Optional[list[BlackBoxTechnique]] = None,
        *,
        use_llm: bool | None = None,
    ) -> dict:
        """Generate test cases with full coverage tracking and reporting."""
        techniques_to_use = selected_techniques or list(BlackBoxTechnique)
        llm_enabled = self.use_llm if use_llm is None else use_llm

        coverage_items = self.coverage_manager.identify_coverage_items(requirement)

        if selected_techniques:
            for item in coverage_items:
                self.coverage_manager.select_techniques_for_item(item, selected_techniques)
        else:
            for item in coverage_items:
                self.coverage_manager.auto_select_techniques(item)

        llm_coverage: list = []
        if llm_enabled:
            try:
                llm_result = self.llm_generator.generate(
                    requirement, techniques=techniques_to_use
                )
                all_test_cases = llm_result.test_cases
                if llm_result.coverage_items:
                    llm_coverage = llm_result.coverage_items
                    coverage_items = self._merge_coverage_items(
                        coverage_items, llm_result.coverage_items
                    )
            except BlackboxGenerationError as exc:
                logger.warning(
                    "LLM blackbox with coverage failed, falling back to rules: %s",
                    exc,
                )
                all_test_cases = self._generate_rule_based(requirement, techniques_to_use)
        else:
            all_test_cases = self._generate_rule_based(requirement, techniques_to_use)

        for test_case in all_test_cases:
            for coverage_item_id in test_case.coverage_items:
                matching_item = next(
                    (item for item in coverage_items if item.id == coverage_item_id),
                    None,
                )
                if matching_item:
                    self.coverage_manager.mark_covered(matching_item, test_case.id)

        coverage_report = self.coverage_manager.generate_coverage_report(coverage_items)

        return {
            "coverage_items": coverage_items,
            "test_cases": all_test_cases,
            "coverage_report": coverage_report,
            "llm_coverage_items": llm_coverage,
        }

    def _generate(
        self,
        requirement: StructuredRequirement,
        techniques: list[BlackBoxTechnique],
        *,
        use_llm: bool | None = None,
    ) -> list[TestCase]:
        llm_enabled = self.use_llm if use_llm is None else use_llm
        if llm_enabled:
            try:
                return self.llm_generator.generate_test_cases(
                    requirement, techniques=techniques
                )
            except BlackboxGenerationError as exc:
                logger.warning(
                    "LLM blackbox failed for req=%s, falling back to rules: %s",
                    requirement.id,
                    exc,
                )
        return self._generate_rule_based(requirement, techniques)

    def _generate_rule_based(
        self,
        requirement: StructuredRequirement,
        techniques: list[BlackBoxTechnique],
    ) -> list[TestCase]:
        all_test_cases: list[TestCase] = []
        for technique in techniques:
            generator = self.generators.get(technique)
            if generator:
                all_test_cases.extend(generator.generate(requirement))
        return all_test_cases

    @staticmethod
    def _merge_coverage_items(
        baseline: list,
        llm_items: list,
    ) -> list:
        """Prefer LLM items when ids overlap; append novel LLM items."""
        by_id = {item.id: item for item in baseline}
        for item in llm_items:
            by_id[item.id] = item
        return list(by_id.values())

    def get_technique_info(self) -> dict:
        """Get information about available testing techniques."""
        return {
            "EP": {
                "name": "Equivalence Partitioning",
                "description": "Divides input data into equivalence classes and tests representative values from each class",
                "standard": "ISO 29119-4",
                "best_for": "Testing input validation and data range handling",
                "generation": "LLM-first with rule fallback",
            },
            "BVA": {
                "name": "Boundary Value Analysis",
                "description": "Tests values at, just below, and just above boundaries where errors frequently occur",
                "standard": "ISO 29119-4",
                "best_for": "Testing numerical ranges and boundary conditions",
                "generation": "LLM-first with rule fallback",
            },
            "DT": {
                "name": "Decision Table Testing",
                "description": "Tests all combinations of conditions to ensure correct business logic implementation",
                "standard": "ISO 29119-4",
                "best_for": "Testing complex business rules and conditional logic",
                "generation": "LLM-first with rule fallback",
            },
        }
