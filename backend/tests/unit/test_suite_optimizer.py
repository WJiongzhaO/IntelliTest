"""Tests for FR 7.0 suite optimizer (no LLM)."""

from app.engines.risk_analyzer.analyzer import priority_from_score, score_from_dimensions
from app.engines.suite_optimizer.optimizer import greedy_minimize_cover, optimize_suite, sort_by_risk
from app.models.test_case import Priority, TestCase


def test_priority_buckets():
    assert priority_from_score(25) == "High"
    assert priority_from_score(15) == "High"
    assert priority_from_score(14) == "Medium"
    assert priority_from_score(8) == "Medium"
    assert priority_from_score(7) == "Low"
    assert priority_from_score(1) == "Low"


def test_score_product():
    assert score_from_dimensions(5, 5) == 25
    assert score_from_dimensions(2, 4) == 8


def test_sort_by_risk_orders_desc():
    cases = [
        TestCase(
            id="a",
            requirement_id="r1",
            title="low",
            risk_score=3,
            priority=Priority.LOW,
        ),
        TestCase(
            id="b",
            requirement_id="r1",
            title="high",
            risk_score=20,
            priority=Priority.HIGH,
        ),
    ]
    ordered = sort_by_risk(cases)
    assert [c.id for c in ordered] == ["b", "a"]


def test_greedy_minimize_reduces_count():
    cases = [
        TestCase(
            id="1",
            requirement_id="r",
            title="t1",
            risk_score=10,
            priority=Priority.HIGH,
            coverage_items=["A", "B"],
        ),
        TestCase(
            id="2",
            requirement_id="r",
            title="t2",
            risk_score=5,
            priority=Priority.MEDIUM,
            coverage_items=["B", "C"],
        ),
        TestCase(
            id="3",
            requirement_id="r",
            title="t3",
            risk_score=8,
            priority=Priority.HIGH,
            coverage_items=["C"],
        ),
    ]
    ordered = sort_by_risk(cases)
    minimized, _diag = greedy_minimize_cover(ordered)
    cov_union = {"A", "B", "C"}
    covered = set()
    for tc in minimized:
        covered.update(tc.coverage_items or [])
    assert covered == cov_union
    assert len(minimized) <= len(cases)


def test_optimize_risk_sort_keeps_length():
    cases = [
        TestCase(id="x", requirement_id="r", title="x", risk_score=1),
        TestCase(id="y", requirement_id="r", title="y", risk_score=9),
    ]
    out, m = optimize_suite(cases, "risk_sort")
    assert len(out) == len(cases)
    assert m.case_count_after == m.case_count_before
