"""Equivalence Partitioning (EP) test case generator.

Implements ISO 29119-4 Equivalence Partitioning technique.
Divides input data into equivalence classes and selects representative values.
"""

from typing import Optional

from app.engines.blackbox_generator.base import BaseBlackBoxGenerator
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, Priority, TestCase


class EquivalencePartitioningGenerator(BaseBlackBoxGenerator):
    """Generates test cases using Equivalence Partitioning technique.
    
    EP divides input domain into equivalence classes where the system
    is expected to behave similarly. One representative value from each
    class is sufficient to test that class.
    """
    
    @property
    def technique(self) -> BlackBoxTechnique:
        return BlackBoxTechnique.EP
    
    def generate(
        self,
        requirement: StructuredRequirement,
        coverage_items: Optional[list[str]] = None
    ) -> list[TestCase]:
        """Generate EP-based test cases from structured requirement.
        
        Analyzes input fields and data ranges to identify valid and invalid
        equivalence classes, then generates test cases for each class.
        """
        test_cases = []
        test_index = 1
        
        # Process each input field
        for field in requirement.input_fields:
            # Find related data ranges for this field
            related_ranges = self._extract_related_ranges(field, requirement.data_ranges)
            
            if related_ranges:
                # Generate test cases for identified ranges
                for range_desc in related_ranges:
                    ep_class = self._classify_equivalence_class(range_desc)
                    test_case = self._create_ep_test_case(
                        requirement_id=requirement.id,
                        field=field,
                        range_description=range_desc,
                        ep_class=ep_class,
                        index=test_index,
                        expected_actions=requirement.expected_actions
                    )
                    test_cases.append(test_case)
                    test_index += 1
            else:
                # If no explicit ranges, create basic valid/invalid classes
                test_cases.extend(self._generate_basic_ep_tests(
                    requirement_id=requirement.id,
                    field=field,
                    index=test_index,
                    expected_actions=requirement.expected_actions
                ))
                test_index += 2  # Increment for two test cases (valid + invalid)
        
        return test_cases
    
    def _extract_related_ranges(self, field: str, data_ranges: list[str]) -> list[str]:
        """Extract data ranges related to a specific input field.
        
        Args:
            field: Input field name
            data_ranges: List of all data range descriptions
            
        Returns:
            List of relevant range descriptions
        """
        related = []
        field_lower = field.lower()
        
        for range_desc in data_ranges:
            if field_lower in range_desc.lower():
                related.append(range_desc)
        
        return related
    
    def _classify_equivalence_class(self, range_description: str) -> str:
        """Classify a range description as valid or invalid equivalence class.
        
        Args:
            range_description: Description of the data range
            
        Returns:
            Classification: 'valid' or 'invalid'
        """
        desc_lower = range_description.lower()
        
        # Keywords indicating invalid ranges
        invalid_keywords = ['invalid', 'error', 'not allowed', 'exceed', 'below', 
                          'outside', 'negative', 'empty', 'null']
        
        for keyword in invalid_keywords:
            if keyword in desc_lower:
                return 'invalid'
        
        return 'valid'
    
    def _create_ep_test_case(
        self,
        requirement_id: str,
        field: str,
        range_description: str,
        ep_class: str,
        index: int,
        expected_actions: list[str]
    ) -> TestCase:
        """Create a single EP test case.
        
        Args:
            requirement_id: Source requirement ID
            field: Input field being tested
            range_description: Description of the equivalence class
            ep_class: 'valid' or 'invalid'
            index: Test case sequence number
            expected_actions: Expected system actions
            
        Returns:
            Generated TestCase
        """
        test_id = self._generate_test_id(requirement_id, index)
        
        # Determine priority based on equivalence class
        priority = Priority.HIGH if ep_class == 'invalid' else Priority.MEDIUM
        
        # Create descriptive title
        title = f"EP Test: {field} - {ep_class.capitalize()} equivalence class"
        
        # Extract representative test data from range description
        test_data = self._extract_representative_value(range_description, ep_class)
        
        # Define expected result
        if ep_class == 'valid':
            expected_result = f"System should accept the input and {expected_actions[0] if expected_actions else 'process normally'}"
        else:
            expected_result = f"System should reject the input with appropriate error message"
        
        return TestCase(
            id=test_id,
            requirement_id=requirement_id,
            title=title,
            precondition=f"User is on the input form for {field}",
            test_steps=[
                f"Enter {test_data} into the {field} field",
                "Submit the form",
                "Verify system response"
            ],
            test_data=test_data,
            expected_result=expected_result,
            technique=self.technique,
            priority=priority,
            coverage_items=[f"{field}_{ep_class}_class"],
            modified_by_user=False
        )
    
    def _extract_representative_value(self, range_description: str, ep_class: str) -> str:
        """Extract a representative test value from range description.
        
        Args:
            range_description: Description of the data range
            ep_class: 'valid' or 'invalid'
            
        Returns:
            Representative test value
        """
        # This is a simplified extraction - in production, use more sophisticated parsing
        desc_lower = range_description.lower()
        
        if ep_class == 'valid':
            # Try to extract a typical valid value
            if 'between' in desc_lower or 'range' in desc_lower:
                return "typical_valid_value"
            elif 'positive' in desc_lower:
                return "100"
            else:
                return "valid_input"
        else:
            # Invalid class representative
            if 'negative' in desc_lower:
                return "-1"
            elif 'empty' in desc_lower or 'null' in desc_lower:
                return ""
            elif 'exceed' in desc_lower:
                return "999999"
            else:
                return "invalid_input"
    
    def _generate_basic_ep_tests(
        self,
        requirement_id: str,
        field: str,
        index: int,
        expected_actions: list[str]
    ) -> list[TestCase]:
        """Generate basic valid/invalid EP tests when no ranges are specified.
        
        Args:
            requirement_id: Source requirement ID
            field: Input field name
            index: Starting test case index
            expected_actions: Expected system actions
            
        Returns:
            List of two test cases (valid and invalid)
        """
        test_cases = []
        
        # Valid equivalence class
        valid_test = TestCase(
            id=self._generate_test_id(requirement_id, index),
            requirement_id=requirement_id,
            title=f"EP Test: {field} - Valid input",
            precondition=f"User is on the input form for {field}",
            test_steps=[
                f"Enter a valid value into the {field} field",
                "Submit the form",
                "Verify system accepts the input"
            ],
            test_data="valid_example",
            expected_result=f"System should accept and {expected_actions[0] if expected_actions else 'process normally'}",
            technique=self.technique,
            priority=Priority.MEDIUM,
            coverage_items=[f"{field}_valid_class"],
            modified_by_user=False
        )
        test_cases.append(valid_test)
        
        # Invalid equivalence class
        invalid_test = TestCase(
            id=self._generate_test_id(requirement_id, index + 1),
            requirement_id=requirement_id,
            title=f"EP Test: {field} - Invalid input",
            precondition=f"User is on the input form for {field}",
            test_steps=[
                f"Enter an invalid value into the {field} field",
                "Submit the form",
                "Verify system rejects the input"
            ],
            test_data="invalid_example",
            expected_result="System should reject with appropriate error message",
            technique=self.technique,
            priority=Priority.HIGH,
            coverage_items=[f"{field}_invalid_class"],
            modified_by_user=False
        )
        test_cases.append(invalid_test)
        
        return test_cases
