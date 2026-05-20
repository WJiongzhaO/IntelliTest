"""Boundary Value Analysis (BVA) test case generator.

Implements ISO 29119-4 Boundary Value Analysis technique.
Tests values at, just below, and just above boundaries of input ranges.
"""

import re
from typing import Optional

from app.engines.blackbox_generator.base import BaseBlackBoxGenerator
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, Priority, TestCase


class BoundaryValueAnalysisGenerator(BaseBlackBoxGenerator):
    """Generates test cases using Boundary Value Analysis technique.
    
    BVA focuses on testing boundary values because errors often occur at 
    the edges of input domains. For each boundary, we test:
    - The boundary value itself
    - Just below the boundary (min - 1)
    - Just above the boundary (max + 1)
    """
    
    @property
    def technique(self) -> BlackBoxTechnique:
        return BlackBoxTechnique.BVA
    
    def generate(
        self,
        requirement: StructuredRequirement,
        coverage_items: Optional[list[str]] = None
    ) -> list[TestCase]:
        """Generate BVA-based test cases from structured requirement.
        
        Analyzes data ranges to identify numerical boundaries and generates
        test cases for boundary values.
        """
        test_cases = []
        test_index = 1
        
        # Process each data range to find boundaries
        for range_desc in requirement.data_ranges:
            boundaries = self._extract_boundaries(range_desc)
            
            if boundaries:
                for boundary_info in boundaries:
                    bva_tests = self._generate_boundary_tests(
                        requirement_id=requirement.id,
                        field=self._identify_field_from_range(range_desc, requirement.input_fields),
                        boundary_info=boundary_info,
                        index=test_index,
                        expected_actions=requirement.expected_actions
                    )
                    test_cases.extend(bva_tests)
                    test_index += len(bva_tests)
        
        # If no explicit boundaries found, generate basic boundary tests
        if not test_cases and requirement.input_fields:
            for field in requirement.input_fields[:3]:  # Limit to first 3 fields
                basic_tests = self._generate_basic_bva_tests(
                    requirement_id=requirement.id,
                    field=field,
                    index=test_index,
                    expected_actions=requirement.expected_actions
                )
                test_cases.extend(basic_tests)
                test_index += len(basic_tests)
        
        return test_cases
    
    def _extract_boundaries(self, range_description: str) -> list[dict]:
        """Extract numerical boundaries from range description.
        
        Args:
            range_description: Description containing range/boundary info
            
        Returns:
            List of boundary dictionaries with min/max values
        """
        boundaries = []
        
        # Pattern 1: "between X and Y" or "range X-Y"
        range_pattern = r'(?:between|range|from)\s+(\d+)\s+(?:and|to|-)\s+(\d+)'
        matches = re.findall(range_pattern, range_description, re.IGNORECASE)
        for match in matches:
            min_val, max_val = int(match[0]), int(match[1])
            boundaries.append({
                'type': 'range',
                'min': min_val,
                'max': max_val,
                'description': range_description
            })
        
        # Pattern 2: "minimum X" or "at least X"
        min_pattern = r'(?:minimum|min|at least|>=?)\s*(\d+)'
        min_matches = re.findall(min_pattern, range_description, re.IGNORECASE)
        for match in min_matches:
            min_val = int(match)
            boundaries.append({
                'type': 'minimum',
                'min': min_val,
                'description': range_description
            })
        
        # Pattern 3: "maximum X" or "at most X"
        max_pattern = r'(?:maximum|max|at most|<=?)\s*(\d+)'
        max_matches = re.findall(max_pattern, range_description, re.IGNORECASE)
        for match in max_matches:
            max_val = int(match)
            boundaries.append({
                'type': 'maximum',
                'max': max_val,
                'description': range_description
            })
        
        return boundaries
    
    def _identify_field_from_range(self, range_desc: str, input_fields: list[str]) -> str:
        """Identify which input field a range description refers to.
        
        Args:
            range_desc: Range description text
            input_fields: List of available input fields
            
        Returns:
            Matching field name or first field as default
        """
        desc_lower = range_desc.lower()
        for field in input_fields:
            if field.lower() in desc_lower:
                return field
        return input_fields[0] if input_fields else "unknown_field"
    
    def _generate_boundary_tests(
        self,
        requirement_id: str,
        field: str,
        boundary_info: dict,
        index: int,
        expected_actions: list[str]
    ) -> list[TestCase]:
        """Generate test cases for a specific boundary.
        
        Args:
            requirement_id: Source requirement ID
            field: Input field being tested
            boundary_info: Boundary information (type, min, max)
            index: Starting test case index
            expected_actions: Expected system actions
            
        Returns:
            List of BVA test cases
        """
        test_cases = []
        boundary_type = boundary_info['type']
        
        if boundary_type == 'range':
            min_val = boundary_info['min']
            max_val = boundary_info['max']
            
            # Test minimum boundary
            test_cases.extend([
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="min_below",
                    value=min_val - 1,
                    is_valid=False,
                    index=index,
                    expected_actions=expected_actions,
                    description=f"Below minimum boundary ({min_val - 1})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="min_at",
                    value=min_val,
                    is_valid=True,
                    index=index + 1,
                    expected_actions=expected_actions,
                    description=f"At minimum boundary ({min_val})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="min_above",
                    value=min_val + 1,
                    is_valid=True,
                    index=index + 2,
                    expected_actions=expected_actions,
                    description=f"Just above minimum boundary ({min_val + 1})"
                ),
            ])
            
            # Test maximum boundary
            test_cases.extend([
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="max_below",
                    value=max_val - 1,
                    is_valid=True,
                    index=index + 3,
                    expected_actions=expected_actions,
                    description=f"Just below maximum boundary ({max_val - 1})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="max_at",
                    value=max_val,
                    is_valid=True,
                    index=index + 4,
                    expected_actions=expected_actions,
                    description=f"At maximum boundary ({max_val})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="max_above",
                    value=max_val + 1,
                    is_valid=False,
                    index=index + 5,
                    expected_actions=expected_actions,
                    description=f"Above maximum boundary ({max_val + 1})"
                ),
            ])
        
        elif boundary_type == 'minimum':
            min_val = boundary_info['min']
            test_cases.extend([
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="min_below",
                    value=min_val - 1,
                    is_valid=False,
                    index=index,
                    expected_actions=expected_actions,
                    description=f"Below minimum ({min_val - 1})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="min_at",
                    value=min_val,
                    is_valid=True,
                    index=index + 1,
                    expected_actions=expected_actions,
                    description=f"At minimum ({min_val})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="min_above",
                    value=min_val + 1,
                    is_valid=True,
                    index=index + 2,
                    expected_actions=expected_actions,
                    description=f"Above minimum ({min_val + 1})"
                ),
            ])
        
        elif boundary_type == 'maximum':
            max_val = boundary_info['max']
            test_cases.extend([
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="max_below",
                    value=max_val - 1,
                    is_valid=True,
                    index=index,
                    expected_actions=expected_actions,
                    description=f"Below maximum ({max_val - 1})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="max_at",
                    value=max_val,
                    is_valid=True,
                    index=index + 1,
                    expected_actions=expected_actions,
                    description=f"At maximum ({max_val})"
                ),
                self._create_bva_test_case(
                    requirement_id=requirement_id,
                    field=field,
                    boundary_type="max_above",
                    value=max_val + 1,
                    is_valid=False,
                    index=index + 2,
                    expected_actions=expected_actions,
                    description=f"Above maximum ({max_val + 1})"
                ),
            ])
        
        return test_cases
    
    def _create_bva_test_case(
        self,
        requirement_id: str,
        field: str,
        boundary_type: str,
        value: int,
        is_valid: bool,
        index: int,
        expected_actions: list[str],
        description: str
    ) -> TestCase:
        """Create a single BVA test case.
        
        Args:
            requirement_id: Source requirement ID
            field: Input field being tested
            boundary_type: Type of boundary test (min_at, max_above, etc.)
            value: Test value
            is_valid: Whether this value should be accepted
            index: Test case sequence number
            expected_actions: Expected system actions
            description: Human-readable description
            
        Returns:
            Generated TestCase
        """
        test_id = self._generate_test_id(requirement_id, index)
        
        priority = Priority.HIGH if not is_valid else Priority.MEDIUM
        
        title = f"BVA Test: {field} - {description}"
        
        if is_valid:
            expected_result = f"System should accept the value {value} and {expected_actions[0] if expected_actions else 'process normally'}"
        else:
            expected_result = f"System should reject the value {value} with appropriate error message"
        
        return TestCase(
            id=test_id,
            requirement_id=requirement_id,
            title=title,
            precondition=f"User is on the input form for {field}",
            test_steps=[
                f"Enter {value} into the {field} field",
                "Submit the form",
                "Verify system response"
            ],
            test_data=str(value),
            expected_result=expected_result,
            technique=self.technique,
            priority=priority,
            coverage_items=[f"{field}_{boundary_type}"],
            modified_by_user=False
        )
    
    def _generate_basic_bva_tests(
        self,
        requirement_id: str,
        field: str,
        index: int,
        expected_actions: list[str]
    ) -> list[TestCase]:
        """Generate basic BVA tests when no explicit boundaries are found.
        
        Uses assumed boundaries: 0 and 100 as typical defaults.
        """
        test_cases = []
        
        # Assume typical range 0-100
        assumed_boundaries = [
            {'type': 'range', 'min': 0, 'max': 100, 'description': f"Assumed range for {field}"}
        ]
        
        for boundary in assumed_boundaries:
            tests = self._generate_boundary_tests(
                requirement_id=requirement_id,
                field=field,
                boundary_info=boundary,
                index=index,
                expected_actions=expected_actions
            )
            test_cases.extend(tests)
        
        return test_cases
