"""Unit tests for FR 6.0 export service."""

import json

from app.engines.export_service.exporter import (
    ExportArtifact,
    ExportOptions,
    export_artifact,
)
from app.models.test_case import CoverageItem, TestCase, TestSuite


def _sample_artifact() -> ExportArtifact:
    case = TestCase(
        id="TC-001",
        requirement_id="REQ-001",
        title="Valid login",
        test_steps=["Open login page", "Submit valid credentials"],
        expected_result="Dashboard is displayed",
        priority="High",
        risk_score=20,
        coverage_items=["COV-001"],
        modified_by_user=True,
    )
    coverage = CoverageItem(
        id="COV-001",
        requirement_id="REQ-001",
        description="Valid login path",
        item_type="condition",
        covered_by_test_cases=["TC-001"],
    )
    return ExportArtifact(test_cases=[case], coverage_items=[coverage])


def _sample_suite_artifact(options: ExportOptions) -> ExportArtifact:
    case = TestCase(
        id="TC-001",
        requirement_id="REQ-001",
        title="Valid login",
        test_steps=["Open login page", "Submit valid credentials"],
        expected_result="Dashboard is displayed",
        priority="High",
        risk_score=20,
        coverage_items=["COV-001"],
        modified_by_user=True,
    )
    suite = TestSuite(id="SUITE-001", name="Review suite", test_cases=[case])
    return ExportArtifact(suite=suite, test_cases=[case], options=options)


def test_export_json_contains_schema_and_case() -> None:
    result = export_artifact(_sample_artifact(), "json")

    assert result.filename.endswith(".json")
    assert b"IntelliTest.FR6.Export.v1" in result.content
    assert b"TC-001" in result.content


def test_export_csv_contains_case_columns() -> None:
    result = export_artifact(_sample_artifact(), "csv")
    text = result.content.decode("utf-8-sig")

    assert result.filename.endswith(".csv")
    assert "test_case_id" in text
    assert "TC-001" in text


def test_export_xlsx_returns_workbook_bytes() -> None:
    result = export_artifact(_sample_artifact(), "xlsx")

    assert result.filename.endswith(".xlsx")
    assert result.content.startswith(b"PK")


def test_export_csv_respects_coverage_option() -> None:
    artifact = _sample_suite_artifact(ExportOptions(include_coverage=False))
    result = export_artifact(artifact, "csv")
    text = result.content.decode("utf-8-sig")

    assert "coverage_items" not in text.splitlines()[0]
    assert "COV-001" not in text


def test_export_json_respects_coverage_option_inside_suite() -> None:
    artifact = _sample_suite_artifact(ExportOptions(include_coverage=False))
    result = export_artifact(artifact, "json")
    payload = json.loads(result.content.decode("utf-8"))

    assert payload["coverage_items"] == []
    assert payload["summary"]["coverage_item_count"] == 0
    assert "coverage_items" not in payload["test_cases"][0]
    assert "coverage_items" not in payload["suite"]["test_cases"][0]
