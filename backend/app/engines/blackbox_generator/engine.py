"""Main black-box test generation engine.

Orchestrates the three ISO 29119-4 techniques (EP, BVA, DT) and provides
a unified interface for generating comprehensive black-box test suites.
"""

from typing import Optional

from app.engines.blackbox_generator.boundary_value_analysis import BoundaryValueAnalysisGenerator
from app.engines.blackbox_generator.coverage_manager import CoverageManager
from app.engines.blackbox_generator.decision_table import DecisionTableGenerator
from app.engines.blackbox_generator.equivalence_partitioning import EquivalencePartitioningGenerator
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, TestCase


class BlackBoxTestGenerator:
    """Main orchestrator for black-box test case generation.
    
    Combines EP, BVA, and DT techniques to generate comprehensive
    test suites according to ISO 29119-4 standards.
    """
    
    def __init__(self):
        """Initialize the generator with all technique implementations."""
        self.ep_generator = EquivalencePartitioningGenerator()
        self.bva_generator = BoundaryValueAnalysisGenerator()
        self.dt_generator = DecisionTableGenerator()
        self.coverage_manager = CoverageManager()
        
        # Map techniques to their generators
        self.generators = {
            BlackBoxTechnique.EP: self.ep_generator,
            BlackBoxTechnique.BVA: self.bva_generator,
            BlackBoxTechnique.DT: self.dt_generator,
        }
    
    def generate_all_techniques(
        self,
        requirement: StructuredRequirement
    ) -> list[TestCase]:
        """Generate test cases using all three black-box techniques.
        
        Args:
            requirement: The structured requirement to test
            
        Returns:
            Combined list of test cases from all techniques
        """
        all_test_cases = []
        
        # Generate EP test cases
        ep_tests = self.ep_generator.generate(requirement)
        all_test_cases.extend(ep_tests)
        
        # Generate BVA test cases
        bva_tests = self.bva_generator.generate(requirement)
        all_test_cases.extend(bva_tests)
        
        # Generate DT test cases
        dt_tests = self.dt_generator.generate(requirement)
        all_test_cases.extend(dt_tests)
        
        return all_test_cases
    
    def generate_specific_technique(
        self,
        requirement: StructuredRequirement,
        technique: BlackBoxTechnique
    ) -> list[TestCase]:
        """Generate test cases using a specific technique.
        
        Args:
            requirement: The structured requirement to test
            technique: The specific technique to use
            
        Returns:
            List of test cases from the specified technique
        """
        generator = self.generators.get(technique)
        if not generator:
            raise ValueError(f"Unsupported technique: {technique}")
        
        return generator.generate(requirement)
    
    def generate_with_coverage_tracking(
        self,
        requirement: StructuredRequirement,
        selected_techniques: Optional[list[BlackBoxTechnique]] = None
    ) -> dict:
        """Generate test cases with full coverage tracking.
        
        This is the main method that provides comprehensive results including
        coverage items, test cases, and coverage metrics.
        
        Args:
            requirement: The structured requirement to test
            selected_techniques: Optional list of techniques to use (default: all)
            
        Returns:
            Dictionary containing:
                - coverage_items: List of identified coverage items
                - test_cases: Generated test cases
                - coverage_report: Coverage statistics
        """
        # Step 1: Identify coverage items
        coverage_items = self.coverage_manager.identify_coverage_items(requirement)
        
        # Step 2: Auto-select techniques for each item if not specified
        if selected_techniques:
            for item in coverage_items:
                self.coverage_manager.select_techniques_for_item(item, selected_techniques)
        else:
            for item in coverage_items:
                self.coverage_manager.auto_select_techniques(item)
        
        # Step 3: Generate test cases based on selected techniques
        techniques_to_use = selected_techniques or list(BlackBoxTechnique)
        all_test_cases = []
        
        for technique in techniques_to_use:
            tests = self.generate_specific_technique(requirement, technique)
            all_test_cases.extend(tests)
        
        # Step 4: Update coverage tracking
        for test_case in all_test_cases:
            for coverage_item_id in test_case.coverage_items:
                matching_item = next(
                    (item for item in coverage_items if item.id == coverage_item_id),
                    None
                )
                if matching_item:
                    self.coverage_manager.mark_covered(matching_item, test_case.id)
        
        # Step 5: Generate coverage report
        coverage_report = self.coverage_manager.generate_coverage_report(coverage_items)
        
        return {
            'coverage_items': coverage_items,
            'test_cases': all_test_cases,
            'coverage_report': coverage_report
        }
    
    def get_technique_info(self) -> dict:
        """Get information about available testing techniques.
        
        Returns:
            Dictionary describing each technique and its purpose
        """
        return {
            'EP': {
                'name': 'Equivalence Partitioning',
                'description': 'Divides input data into equivalence classes and tests representative values from each class',
                'standard': 'ISO 29119-4',
                'best_for': 'Testing input validation and data range handling'
            },
            'BVA': {
                'name': 'Boundary Value Analysis',
                'description': 'Tests values at, just below, and just above boundaries where errors frequently occur',
                'standard': 'ISO 29119-4',
                'best_for': 'Testing numerical ranges and boundary conditions'
            },
            'DT': {
                'name': 'Decision Table Testing',
                'description': 'Tests all combinations of conditions to ensure correct business logic implementation',
                'standard': 'ISO 29119-4',
                'best_for': 'Testing complex business rules and conditional logic'
            }
        }
