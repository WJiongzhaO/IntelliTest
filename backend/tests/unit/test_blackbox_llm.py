"""Unit tests for LLM black-box schema parsing."""

import pytest

from app.engines.blackbox_generator import BlackBoxTestGenerator
from app.engines.blackbox_generator.llm_generator import LLMBlackBoxGenerator
from app.engines.blackbox_generator.schema import (
    parse_test_cases,
    validate_blackbox_payload,
)
from app.exceptions import BlackboxGenerationError
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique


@pytest.fixture
def sample_payload():
    return {
        "analysis": {
            "ep_partitions": [
                {
                    "field": "age",
                    "class": "valid",
                    "description": "Adult age",
                    "representative_value": "25",
                }
            ],
            "bva_applicable": True,
            "bva_boundaries": [{"field": "age", "boundary_type": "min", "values": ["17", "18", "19"]}],
            "dt_conditions": ["age >= 18"],
            "dt_rules": [{"conditions": {"age >= 18": True}, "action": "Register", "expected_outcome": "OK"}],
        },
        "coverage_items": [
            {
                "id": "CI_REQ001_field_age",
                "description": "Age field",
                "item_type": "input_field",
                "selected_techniques": ["EP"],
            }
        ],
        "test_cases": [
            {
                "technique": "EP",
                "title": "EP valid age",
                "test_steps": ["Enter age 25", "Submit"],
                "test_data": "age=25",
                "expected_result": "Registration succeeds",
                "priority": "High",
                "coverage_items": ["CI_REQ001_field_age"],
            },
            {
                "technique": "BVA",
                "title": "BVA min boundary",
                "test_steps": ["Enter age 18", "Submit"],
                "test_data": "age=18",
                "expected_result": "Registration succeeds",
                "priority": "Medium",
                "coverage_items": [],
            },
            {
                "technique": "DT",
                "title": "DT adult rule",
                "test_steps": ["Enter age 25", "Submit"],
                "test_data": "age=25",
                "expected_result": "Registration succeeds",
                "priority": "Medium",
                "coverage_items": [],
            },
        ],
    }


@pytest.fixture
def sample_requirement():
    return StructuredRequirement(
        id="REQ001",
        raw_text="Registration with age 18-120",
        input_fields=["age"],
        data_ranges=["Age 18-120"],
        conditions=["age >= 18"],
        expected_actions=["Register user"],
        risk_score=10,
        priority="High",
    )


class TestBlackboxSchema:
    def test_validate_success(self, sample_payload):
        validate_blackbox_payload(
            sample_payload,
            requested_techniques=list(BlackBoxTechnique),
        )

    def test_validate_missing_technique(self, sample_payload):
        sample_payload["test_cases"] = sample_payload["test_cases"][:1]
        with pytest.raises(BlackboxGenerationError, match="missing requested techniques"):
            validate_blackbox_payload(
                sample_payload,
                requested_techniques=list(BlackBoxTechnique),
            )

    def test_bva_skip_when_not_applicable(self, sample_payload):
        sample_payload["analysis"]["bva_applicable"] = False
        sample_payload["analysis"]["bva_skip_reason"] = "No boundaries"
        sample_payload["test_cases"] = [
            tc for tc in sample_payload["test_cases"] if tc["technique"] != "BVA"
        ]
        validate_blackbox_payload(
            sample_payload,
            requested_techniques=list(BlackBoxTechnique),
        )

    def test_parse_test_cases(self, sample_payload, sample_requirement):
        cases = parse_test_cases(
            sample_payload,
            sample_requirement,
            requested_techniques=list(BlackBoxTechnique),
        )
        assert len(cases) == 3
        assert {c.technique.value for c in cases} == {"EP", "BVA", "DT"}
        assert cases[0].id == "REQ001_EP_001"


class MockLLM:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def complete_json(self, system, user, *, temperature=0.0):
        self.calls += 1
        return self.payload


class TestLLMBlackBoxEngine:
    def test_engine_uses_llm_when_enabled(self, sample_payload, sample_requirement):
        mock = MockLLM(sample_payload)
        engine = BlackBoxTestGenerator(use_llm=True)
        engine.llm_generator = LLMBlackBoxGenerator(llm=mock)

        cases = engine.generate_all_techniques(sample_requirement)
        assert len(cases) == 3
        assert mock.calls == 1

    def test_engine_falls_back_on_llm_failure(self, sample_requirement):
        class FailingLLM:
            def complete_json(self, *args, **kwargs):
                raise Exception("LLM down")

        engine = BlackBoxTestGenerator(use_llm=True)
        engine.llm_generator = LLMBlackBoxGenerator(llm=FailingLLM())

        cases = engine.generate_all_techniques(sample_requirement)
        assert len(cases) > 0
        techniques = {c.technique.value for c in cases}
        assert "EP" in techniques
