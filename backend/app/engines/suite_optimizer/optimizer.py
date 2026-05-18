"""FR 7.0 — Test suite optimization (risk ordering + greedy coverage minimization)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.test_case import Priority, TestCase
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

OptimizationStrategy = Literal["risk_sort", "minimize_coverage", "risk_then_minimize"]


class OptimizationMetrics(BaseModel):
    """Before/after figures for API responses."""

    case_count_before: int = Field(ge=0)
    case_count_after: int = Field(ge=0)
    coverage_items_total: int = Field(
        ge=0, description="Distinct coverage items in universe for minimization"
    )
    coverage_ratio_before: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of universe covered by original suite",
    )
    coverage_ratio_after: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of universe covered by optimized suite",
    )
    strategy_applied: OptimizationStrategy


def _risk_sort_key(tc: TestCase) -> tuple[int, int, str]:
    """Higher risk first; missing scores treated as 0."""
    score = tc.risk_score if tc.risk_score is not None else 0
    prio_order = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}.get(tc.priority, 0)
    return (score, prio_order, tc.id)


def sort_by_risk(test_cases: list[TestCase]) -> list[TestCase]:
    """Order cases by risk_score desc, then priority, then id."""
    return sorted(test_cases, key=_risk_sort_key, reverse=True)


def _build_coverage_universe(
    test_cases: list[TestCase],
    explicit: list[str] | None,
) -> list[str]:
    if explicit is not None:
        return sorted(set(explicit))
    items: set[str] = set()
    for tc in test_cases:
        items.update(tc.coverage_items or [])
    return sorted(items)


def _covered_subset(test_cases: list[TestCase], universe: set[str]) -> set[str]:
    covered: set[str] = set()
    for tc in test_cases:
        for c in tc.coverage_items or []:
            if c in universe:
                covered.add(c)
    return covered


def greedy_minimize_cover(
    test_cases: list[TestCase],
    *,
    coverage_universe: list[str] | None = None,
) -> tuple[list[TestCase], dict]:
    """Pick a small subset that still covers the same universe (greedy set cover heuristic).

    Tie-breaking: more newly covered items, then higher risk_score, then lexicographic id.

    Args:
        test_cases: Full candidate list (typically pre-sorted by risk).
        coverage_universe: Optional explicit list of coverage item IDs; default union of cases.

    Returns:
        Tuple of (selected cases in pick order, diagnostic dict).
    """
    universe_list = _build_coverage_universe(test_cases, coverage_universe)
    universe = set(universe_list)

    if not universe:
        logger.info("Greedy minimize: empty universe — returning input order unchanged")
        return list(test_cases), {"reason": "empty_universe"}

    remaining = set(universe)
    pool = list(test_cases)
    chosen: list[TestCase] = []

    while remaining and pool:
        best_idx = -1
        best_gain = -1
        best_tie: tuple[int, int, str] = (-1, -1, "")

        for i, tc in enumerate(pool):
            cov = set(tc.coverage_items or [])
            gain = len(cov & remaining)
            score = tc.risk_score if tc.risk_score is not None else 0
            tie = (gain, score, tc.id)
            if tie > best_tie:
                best_tie = tie
                best_gain = gain
                best_idx = i

        if best_idx < 0 or best_gain <= 0:
            break

        picked = pool.pop(best_idx)
        chosen.append(picked)
        cov = set(picked.coverage_items or [])
        remaining -= cov

    return chosen, {"uncovered": sorted(remaining)}


def optimize_suite(
    test_cases: list[TestCase],
    strategy: OptimizationStrategy,
    *,
    coverage_universe: list[str] | None = None,
) -> tuple[list[TestCase], OptimizationMetrics]:
    """Apply requested optimization strategy.

    Args:
        test_cases: Full suite.
        strategy: risk_sort | minimize_coverage | risk_then_minimize.
        coverage_universe: Optional explicit coverage IDs for minimization.

    Returns:
        Optimized suite and metrics comparing before/after.
    """
    universe_list = _build_coverage_universe(test_cases, coverage_universe)
    universe_set = set(universe_list)
    n_uni = len(universe_set)

    def cov_ratio(cases: list[TestCase]) -> float:
        if n_uni == 0:
            return 1.0 if cases else 0.0
        covered = _covered_subset(cases, universe_set)
        return len(covered) / n_uni

    before_count = len(test_cases)
    cov_before = cov_ratio(test_cases)

    if strategy == "risk_sort":
        out = sort_by_risk(test_cases)
        metrics = OptimizationMetrics(
            case_count_before=before_count,
            case_count_after=len(out),
            coverage_items_total=n_uni,
            coverage_ratio_before=cov_before,
            coverage_ratio_after=cov_ratio(out),
            strategy_applied=strategy,
        )
        return out, metrics

    if strategy == "minimize_coverage":
        ordered = sort_by_risk(test_cases)
        out, _diag = greedy_minimize_cover(ordered, coverage_universe=coverage_universe)
        metrics = OptimizationMetrics(
            case_count_before=before_count,
            case_count_after=len(out),
            coverage_items_total=n_uni,
            coverage_ratio_before=cov_before,
            coverage_ratio_after=cov_ratio(out),
            strategy_applied=strategy,
        )
        return out, metrics

    # risk_then_minimize
    ordered = sort_by_risk(test_cases)
    out, _diag = greedy_minimize_cover(ordered, coverage_universe=coverage_universe)
    metrics = OptimizationMetrics(
        case_count_before=before_count,
        case_count_after=len(out),
        coverage_items_total=n_uni,
        coverage_ratio_before=cov_before,
        coverage_ratio_after=cov_ratio(out),
        strategy_applied=strategy,
    )
    return out, metrics
