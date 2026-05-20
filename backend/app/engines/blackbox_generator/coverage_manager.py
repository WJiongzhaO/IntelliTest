"""Coverage item management for black-box testing.

Manages coverage items, technique selection, and traceability between
requirements, coverage items, and test cases.
"""

from typing import Optional
from uuid import uuid4

from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, CoverageItem


class CoverageManager:
    """Manages coverage items for black-box test design.
    
    Provides functionality to:
    - Identify coverage items from structured requirements
    - Select appropriate testing techniques for each coverage item
    - Track which test cases cover which items
    """
    
    def identify_coverage_items(
        self,
        requirement: StructuredRequirement
    ) -> list[CoverageItem]:
        """Identify coverage items from a structured requirement.
        
        Analyzes input fields, data ranges, and conditions to create
        coverage items that need to be tested.
        
        Args:
            requirement: The structured requirement to analyze
            
        Returns:
            List of identified coverage items
        """
        coverage_items = []
        
        # Create coverage items for input fields
        for field in requirement.input_fields:
            item = CoverageItem(
                id=f"CI_{requirement.id}_field_{field.replace(' ', '_')}",
                requirement_id=requirement.id,
                description=f"Test all equivalence classes for input field: {field}",
                item_type="input_field",
                selected_techniques=[BlackBoxTechnique.EP],
                covered_by_test_cases=[]
            )
            coverage_items.append(item)
        
        # Create coverage items for data ranges/boundaries
        for idx, range_desc in enumerate(requirement.data_ranges):
            item = CoverageItem(
                id=f"CI_{requirement.id}_boundary_{idx}",
                requirement_id=requirement.id,
                description=f"Test boundary values for: {range_desc}",
                item_type="boundary",
                selected_techniques=[BlackBoxTechnique.BVA],
                covered_by_test_cases=[]
            )
            coverage_items.append(item)
        
        # Create coverage items for conditions
        for idx, condition in enumerate(requirement.conditions):
            item = CoverageItem(
                id=f"CI_{requirement.id}_condition_{idx}",
                requirement_id=requirement.id,
                description=f"Test decision rules for condition: {condition}",
                item_type="decision_rule",
                selected_techniques=[BlackBoxTechnique.DT],
                covered_by_test_cases=[]
            )
            coverage_items.append(item)
        
        return coverage_items
    
    def select_techniques_for_item(
        self,
        coverage_item: CoverageItem,
        techniques: list[BlackBoxTechnique]
    ) -> CoverageItem:
        """Select testing techniques for a specific coverage item.
        
        Args:
            coverage_item: The coverage item to update
            techniques: List of techniques to apply
            
        Returns:
            Updated coverage item
        """
        coverage_item.selected_techniques = techniques
        return coverage_item
    
    def auto_select_techniques(self, coverage_item: CoverageItem) -> CoverageItem:
        """Automatically select appropriate techniques based on item type.
        
        Args:
            coverage_item: The coverage item to analyze
            
        Returns:
            Coverage item with recommended techniques
        """
        recommended_techniques = []
        
        if coverage_item.item_type == "input_field":
            recommended_techniques.append(BlackBoxTechnique.EP)
        elif coverage_item.item_type == "boundary":
            recommended_techniques.append(BlackBoxTechnique.BVA)
        elif coverage_item.item_type == "decision_rule":
            recommended_techniques.append(BlackBoxTechnique.DT)
        elif coverage_item.item_type == "complex_condition":
            # For complex conditions, use multiple techniques
            recommended_techniques.extend([
                BlackBoxTechnique.EP,
                BlackBoxTechnique.DT
            ])
        
        coverage_item.selected_techniques = recommended_techniques
        return coverage_item
    
    def mark_covered(
        self,
        coverage_item: CoverageItem,
        test_case_id: str
    ) -> CoverageItem:
        """Mark a coverage item as covered by a test case.
        
        Args:
            coverage_item: The coverage item to update
            test_case_id: ID of the test case that covers this item
            
        Returns:
            Updated coverage item
        """
        if test_case_id not in coverage_item.covered_by_test_cases:
            coverage_item.covered_by_test_cases.append(test_case_id)
        return coverage_item
    
    def calculate_coverage_percentage(
        self,
        coverage_items: list[CoverageItem]
    ) -> float:
        """Calculate the percentage of coverage items that are covered.
        
        Args:
            coverage_items: List of all coverage items
            
        Returns:
            Coverage percentage (0-100)
        """
        if not coverage_items:
            return 0.0
        
        covered_count = sum(
            1 for item in coverage_items 
            if len(item.covered_by_test_cases) > 0
        )
        
        return (covered_count / len(coverage_items)) * 100
    
    def get_uncovered_items(
        self,
        coverage_items: list[CoverageItem]
    ) -> list[CoverageItem]:
        """Get coverage items that are not yet covered by any test case.
        
        Args:
            coverage_items: List of all coverage items
            
        Returns:
            List of uncovered coverage items
        """
        return [
            item for item in coverage_items 
            if len(item.covered_by_test_cases) == 0
        ]
    
    def generate_coverage_report(
        self,
        coverage_items: list[CoverageItem]
    ) -> dict:
        """Generate a comprehensive coverage report.
        
        Args:
            coverage_items: List of all coverage items
            
        Returns:
            Dictionary containing coverage statistics and details
        """
        total_items = len(coverage_items)
        covered_items = sum(
            1 for item in coverage_items 
            if len(item.covered_by_test_cases) > 0
        )
        uncovered_items = total_items - covered_items
        
        # Count by type
        type_distribution = {}
        for item in coverage_items:
            item_type = item.item_type
            if item_type not in type_distribution:
                type_distribution[item_type] = {'total': 0, 'covered': 0}
            type_distribution[item_type]['total'] += 1
            if len(item.covered_by_test_cases) > 0:
                type_distribution[item_type]['covered'] += 1
        
        # Technique distribution
        technique_usage = {}
        for item in coverage_items:
            for technique in item.selected_techniques:
                tech_name = technique.value
                if tech_name not in technique_usage:
                    technique_usage[tech_name] = 0
                technique_usage[tech_name] += 1
        
        return {
            'total_coverage_items': total_items,
            'covered_items': covered_items,
            'uncovered_items': uncovered_items,
            'coverage_percentage': self.calculate_coverage_percentage(coverage_items),
            'type_distribution': type_distribution,
            'technique_usage': technique_usage,
            'uncovered_item_details': [
                {
                    'id': item.id,
                    'description': item.description,
                    'type': item.item_type
                }
                for item in self.get_uncovered_items(coverage_items)
            ]
        }
