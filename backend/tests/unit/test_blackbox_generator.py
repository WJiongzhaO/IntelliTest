"""Unit tests for black-box test generators."""

import pytest

from app.engines.blackbox_generator import (
    BlackBoxTestGenerator,
    BoundaryValueAnalysisGenerator,
    DecisionTableGenerator,
    EquivalencePartitioningGenerator,
)
from app.models.requirement import StructuredRequirement


@pytest.fixture
def sample_requirement():
    """Create a sample structured requirement for testing."""
    return StructuredRequirement(
        id="REQ001",
        raw_text="User registration form with age field (18-120), email validation, and premium membership eligibility",
        input_fields=["age", "email", "membership_type"],
        data_ranges=[
            "Age must be between 18 and 120",
            "Email must be valid format",
        ],
        conditions=[
            "If age >= 18 and email is valid",
            "If membership_type is premium",
        ],
        expected_actions=["Register user", "Send confirmation email"],
        risk_score=12,
        priority="High",
    )


class TestEquivalencePartitioning:
    """Tests for EP generator."""

    def test_generate_ep_tests(self, sample_requirement):
        """Test EP test case generation."""
        generator = EquivalencePartitioningGenerator()
        test_cases = generator.generate(sample_requirement)

        assert len(test_cases) > 0
        assert all(tc.technique.value == "EP" for tc in test_cases)
        assert all(tc.requirement_id == "REQ001" for tc in test_cases)

    def test_ep_test_case_structure(self, sample_requirement):
        """Test that EP test cases have proper structure."""
        generator = EquivalencePartitioningGenerator()
        test_cases = generator.generate(sample_requirement)

        for tc in test_cases:
            assert tc.id is not None
            assert tc.title is not None
            assert len(tc.test_steps) > 0
            assert tc.expected_result is not None
            assert len(tc.coverage_items) > 0


class TestBoundaryValueAnalysis:
    """Tests for BVA generator."""

    def test_generate_bva_tests(self, sample_requirement):
        """Test BVA test case generation."""
        generator = BoundaryValueAnalysisGenerator()
        test_cases = generator.generate(sample_requirement)

        assert len(test_cases) > 0
        assert all(tc.technique.value == "BVA" for tc in test_cases)

    def test_bva_boundary_values(self, sample_requirement):
        """Test that BVA generates tests at boundaries."""
        generator = BoundaryValueAnalysisGenerator()
        test_cases = generator.generate(sample_requirement)

        # Should have tests for boundary values like 17, 18, 19, 119, 120, 121
        test_data_values = [tc.test_data for tc in test_cases if tc.test_data]
        assert len(test_data_values) > 0


class TestDecisionTable:
    """Tests for DT generator."""

    def test_generate_dt_tests(self, sample_requirement):
        """Test DT test case generation."""
        generator = DecisionTableGenerator()
        test_cases = generator.generate(sample_requirement)

        assert len(test_cases) > 0
        assert all(tc.technique.value == "DT" for tc in test_cases)

    def test_dt_rule_coverage(self, sample_requirement):
        """Test that DT covers all condition combinations."""
        generator = DecisionTableGenerator()
        test_cases = generator.generate(sample_requirement)

        # Each test case should represent a unique rule
        assert len(test_cases) >= 2  # At least some combinations


class TestBlackBoxEngine:
    """Tests for the main black-box engine."""

    def test_generate_all_techniques(self, sample_requirement):
        """Test generation using all techniques."""
        engine = BlackBoxTestGenerator()
        test_cases = engine.generate_all_techniques(sample_requirement)

        assert len(test_cases) > 0

        # Should have tests from all three techniques
        techniques_used = set(tc.technique.value for tc in test_cases)
        assert "EP" in techniques_used
        assert "BVA" in techniques_used
        assert "DT" in techniques_used

    def test_generate_specific_technique(self, sample_requirement):
        """Test generation using specific technique."""
        from app.models.test_case import BlackBoxTechnique

        engine = BlackBoxTestGenerator()

        ep_tests = engine.generate_specific_technique(
            sample_requirement, BlackBoxTechnique.EP
        )
        assert all(tc.technique == BlackBoxTechnique.EP for tc in ep_tests)

        bva_tests = engine.generate_specific_technique(
            sample_requirement, BlackBoxTechnique.BVA
        )
        assert all(tc.technique == BlackBoxTechnique.BVA for tc in bva_tests)

    def test_generate_with_coverage_tracking(self, sample_requirement):
        """Test generation with coverage tracking."""
        engine = BlackBoxTestGenerator()
        result = engine.generate_with_coverage_tracking(sample_requirement)

        assert 'coverage_items' in result
        assert 'test_cases' in result
        assert 'coverage_report' in result

        assert len(result['coverage_items']) > 0
        assert len(result['test_cases']) > 0
        assert result['coverage_report']['total_coverage_items'] > 0

    def test_get_technique_info(self):
        """Test technique information retrieval."""
        engine = BlackBoxTestGenerator()
        info = engine.get_technique_info()

        assert 'EP' in info
        assert 'BVA' in info
        assert 'DT' in info
        assert info['EP']['standard'] == 'ISO 29119-4'


class TestCoverageManager:
    """Tests for coverage item management."""

    def test_identify_coverage_items(self, sample_requirement):
        """Test coverage item identification."""
        engine = BlackBoxTestGenerator()
        coverage_items = engine.coverage_manager.identify_coverage_items(
            sample_requirement
        )

        assert len(coverage_items) > 0

        # Should have items for input fields, boundaries, and conditions
        item_types = set(item.item_type for item in coverage_items)
        assert len(item_types) >= 1

    def test_coverage_percentage_calculation(self):
        """Test coverage percentage calculation."""
        from app.models.test_case import CoverageItem

        engine = BlackBoxTestGenerator()

        # Create sample coverage items
        items = [
            CoverageItem(
                id="CI1",
                requirement_id="REQ001",
                description="Test item 1",
                item_type="input_field",
                covered_by_test_cases=["TC1"],
            ),
            CoverageItem(
                id="CI2",
                requirement_id="REQ001",
                description="Test item 2",
                item_type="boundary",
                covered_by_test_cases=[],
            ),
        ]

        percentage = engine.coverage_manager.calculate_coverage_percentage(items)
        assert percentage == 50.0

    def test_get_uncovered_items(self):
        """Test retrieval of uncovered items."""
        from app.models.test_case import CoverageItem

        engine = BlackBoxTestGenerator()

        items = [
            CoverageItem(
                id="CI1",
                requirement_id="REQ001",
                description="Covered item",
                item_type="input_field",
                covered_by_test_cases=["TC1"],
            ),
            CoverageItem(
                id="CI2",
                requirement_id="REQ001",
                description="Uncovered item",
                item_type="boundary",
                covered_by_test_cases=[],
            ),
        ]

        uncovered = engine.coverage_manager.get_uncovered_items(items)
        assert len(uncovered) == 1
        assert uncovered[0].id == "CI2"

    def test_generate_coverage_report(self):
        """Test coverage report generation."""
        from app.models.test_case import CoverageItem

        engine = BlackBoxTestGenerator()

        items = [
            CoverageItem(
                id="CI1",
                requirement_id="REQ001",
                description="Item 1",
                item_type="input_field",
                selected_techniques=[],
                covered_by_test_cases=["TC1"],
            ),
            CoverageItem(
                id="CI2",
                requirement_id="REQ001",
                description="Item 2",
                item_type="boundary",
                selected_techniques=[],
                covered_by_test_cases=[],
            ),
        ]

        report = engine.coverage_manager.generate_coverage_report(items)

        assert report['total_coverage_items'] == 2
        assert report['covered_items'] == 1
        assert report['uncovered_items'] == 1
        assert report['coverage_percentage'] == 50.0
