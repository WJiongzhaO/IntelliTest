"""Decision Table (DT) test case generator.

Implements ISO 29119-4 Decision Table Testing technique.
Creates test cases based on combinations of conditions and their outcomes.
"""

from itertools import product
from typing import Optional

from app.engines.blackbox_generator.base import BaseBlackBoxGenerator
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, Priority, TestCase


class DecisionTableGenerator(BaseBlackBoxGenerator):
    """Generates test cases using Decision Table Testing technique.
    
    Decision tables map combinations of conditions (inputs) to actions (outputs).
    Each rule in the table represents a unique combination of condition values,
    and we generate test cases to cover all rules.
    """
    
    @property
    def technique(self) -> BlackBoxTechnique:
        return BlackBoxTechnique.DT
    
    def generate(
        self,
        requirement: StructuredRequirement,
        coverage_items: Optional[list[str]] = None
    ) -> list[TestCase]:
        """Generate DT-based test cases from structured requirement.
        
        Analyzes conditions to build a decision table and generates test cases
        for each rule (condition combination).
        """
        test_cases = []
        
        # Extract conditions and create binary representations
        conditions = self._extract_conditions(requirement.conditions)
        
        if not conditions:
            # If no explicit conditions, derive from input fields
            conditions = self._derive_conditions_from_inputs(requirement.input_fields)
        
        if not conditions:
            return test_cases
        
        # Generate all possible combinations (rules)
        rules = self._generate_rules(conditions)
        
        # Create test case for each rule
        for index, rule in enumerate(rules, start=1):
            test_case = self._create_dt_test_case(
                requirement_id=requirement.id,
                rule_number=index,
                conditions=conditions,
                rule_values=rule,
                expected_actions=requirement.expected_actions,
                total_rules=len(rules)
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _extract_conditions(self, raw_conditions: list[str]) -> list[dict]:
        """Extract and structure conditions from requirement.
        
        Args:
            raw_conditions: List of condition descriptions
            
        Returns:
            List of structured condition dictionaries
        """
        conditions = []
        
        for idx, condition_desc in enumerate(raw_conditions):
            # Try to identify condition type and possible values
            condition_info = self._parse_condition(condition_desc)
            condition_info['id'] = f"C{idx + 1}"
            condition_info['description'] = condition_desc
            conditions.append(condition_info)
        
        return conditions
    
    def _parse_condition(self, condition_desc: str) -> dict:
        """Parse a condition description to extract metadata.
        
        Args:
            condition_desc: Natural language condition description
            
        Returns:
            Dictionary with condition metadata (name, type, values)
        """
        desc_lower = condition_desc.lower()
        
        # Determine if this is a boolean condition or has multiple values
        if any(word in desc_lower for word in ['if', 'when', 'whether', 'is', 'has']):
            # Boolean condition (True/False)
            return {
                'name': self._extract_condition_name(condition_desc),
                'type': 'boolean',
                'values': [True, False]
            }
        elif any(word in desc_lower for word in ['equals', 'in', 'between', 'range']):
            # Range-based condition
            return {
                'name': self._extract_condition_name(condition_desc),
                'type': 'range',
                'values': ['within_range', 'outside_range']
            }
        else:
            # Default to boolean
            return {
                'name': self._extract_condition_name(condition_desc),
                'type': 'boolean',
                'values': [True, False]
            }
    
    def _extract_condition_name(self, condition_desc: str) -> str:
        """Extract a short name from condition description.
        
        Args:
            condition_desc: Full condition description
            
        Returns:
            Simplified condition name
        """
        # Remove common prefixes and clean up
        name = condition_desc.replace('If ', '').replace('When ', '').replace('Whether ', '')
        name = name.strip().rstrip('.')
        
        # Truncate if too long
        if len(name) > 50:
            name = name[:47] + "..."
        
        return name
    
    def _derive_conditions_from_inputs(self, input_fields: list[str]) -> list[dict]:
        """Derive boolean conditions from input fields when no explicit conditions exist.
        
        Args:
            input_fields: List of input field names
            
        Returns:
            List of derived conditions
        """
        conditions = []
        
        for idx, field in enumerate(input_fields[:5]):  # Limit to 5 fields to avoid explosion
            conditions.append({
                'id': f"C{idx + 1}",
                'name': f"{field} is provided",
                'type': 'boolean',
                'values': [True, False],
                'description': f"Whether {field} has a valid value"
            })
        
        return conditions
    
    def _generate_rules(self, conditions: list[dict]) -> list[list]:
        """Generate all possible combinations of condition values (Cartesian product).
        
        Args:
            conditions: List of structured conditions
            
        Returns:
            List of rules, where each rule is a list of values for each condition
        """
        # Get all possible values for each condition
        value_sets = [cond['values'] for cond in conditions]
        
        # Generate Cartesian product
        rules = list(product(*value_sets))
        
        return rules
    
    def _create_dt_test_case(
        self,
        requirement_id: str,
        rule_number: int,
        conditions: list[dict],
        rule_values: list,
        expected_actions: list[str],
        total_rules: int
    ) -> TestCase:
        """Create a test case for a specific decision table rule.
        
        Args:
            requirement_id: Source requirement ID
            rule_number: Rule number in the decision table
            conditions: List of all conditions
            rule_values: Values for this specific rule
            expected_actions: Expected system actions
            total_rules: Total number of rules
            
        Returns:
            Generated TestCase
        """
        test_id = self._generate_test_id(requirement_id, rule_number)
        
        # Build descriptive title
        condition_summary = ", ".join([
            f"{cond['name']}={val}" 
            for cond, val in zip(conditions, rule_values)
        ])
        title = f"DT Test: Rule {rule_number}/{total_rules} - {condition_summary[:80]}"
        
        # Determine priority based on rule complexity
        # Rules with more True values might be higher priority (business-as-usual scenarios)
        true_count = sum(1 for v in rule_values if v is True)
        if true_count == len(rule_values):
            priority = Priority.HIGH  # All conditions met - main path
        elif true_count == 0:
            priority = Priority.LOW   # No conditions met - edge case
        else:
            priority = Priority.MEDIUM
        
        # Build test data description
        test_data_parts = []
        for cond, val in zip(conditions, rule_values):
            if cond['type'] == 'boolean':
                test_data_parts.append(f"{cond['name']}: {'Yes' if val else 'No'}")
            else:
                test_data_parts.append(f"{cond['name']}: {val}")
        
        test_data = "; ".join(test_data_parts)
        
        # Build expected result
        if expected_actions:
            expected_result = f"System should: {expected_actions[0]}"
            if len(expected_actions) > 1:
                expected_result += f"; Also: {', '.join(expected_actions[1:])}"
        else:
            expected_result = "System should process according to the defined business rules"
        
        # Build test steps
        test_steps = [
            f"Set up the following conditions:",
        ]
        for cond, val in zip(conditions, rule_values):
            step_desc = f"  - {cond['name']}: {'Satisfied' if val else 'Not satisfied'}"
            test_steps.append(step_desc)
        
        test_steps.extend([
            "Execute the operation",
            "Verify the system behavior matches the expected outcome"
        ])
        
        # Build coverage items
        coverage_items = [f"rule_{rule_number}"]
        coverage_items.extend([
            f"{cond['id']}_{val}" 
            for cond, val in zip(conditions, rule_values)
        ])
        
        return TestCase(
            id=test_id,
            requirement_id=requirement_id,
            title=title,
            precondition="All prerequisite conditions are met",
            test_steps=test_steps,
            test_data=test_data,
            expected_result=expected_result,
            technique=self.technique,
            priority=priority,
            coverage_items=coverage_items,
            modified_by_user=False
        )
