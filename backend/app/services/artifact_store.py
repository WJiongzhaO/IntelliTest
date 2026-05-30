"""Persist and load test design artifacts in SQLite."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import (
    CoverageItemModel,
    DesignArtifactModel,
    RequirementModel,
    TestCaseModel,
    TestSuiteModel,
)
from app.models.test_case import CoverageItem, Priority, TestCase, TestSuite
from app.utils.requirement_ref import requirement_ref_id


def _case_to_model(
    case: TestCase,
    internal_req_id: str,
    requirement_ref: str,
    suite_id: str,
) -> TestCaseModel:
    priority = case.priority.value if isinstance(case.priority, Priority) else str(case.priority)
    technique = case.technique.value if hasattr(case.technique, "value") else case.technique
    return TestCaseModel(
        id=case.id,
        requirement_id=internal_req_id,
        suite_id=suite_id,
        requirement_ref=requirement_ref,
        title=case.title,
        precondition=case.precondition,
        test_steps=list(case.test_steps or []),
        test_data=case.test_data,
        expected_result=case.expected_result,
        technique=technique,
        priority=priority,
        risk_score=case.risk_score,
        coverage_items=list(case.coverage_items or []),
        modified_by_user=case.modified_by_user,
    )


def _case_from_model(model: TestCaseModel) -> TestCase:
    return TestCase(
        id=model.id,
        requirement_id=model.requirement_ref or model.requirement_id,
        title=model.title,
        precondition=model.precondition,
        test_steps=list(model.test_steps or []),
        test_data=model.test_data,
        expected_result=model.expected_result,
        technique=model.technique,
        priority=model.priority,
        risk_score=model.risk_score,
        coverage_items=list(model.coverage_items or []),
        modified_by_user=model.modified_by_user,
    )


def _coverage_to_model(
    item: CoverageItem,
    internal_req_id: str,
    requirement_ref: str,
) -> CoverageItemModel:
    return CoverageItemModel(
        id=item.id,
        requirement_id=internal_req_id,
        requirement_ref=requirement_ref,
        description=item.description,
        item_type=item.item_type,
        selected_techniques=[t.value if hasattr(t, "value") else t for t in item.selected_techniques],
        covered_by_test_cases=list(item.covered_by_test_cases or []),
    )


def _coverage_from_model(model: CoverageItemModel) -> CoverageItem:
    return CoverageItem(
        id=model.id,
        requirement_id=model.requirement_ref or model.requirement_id,
        description=model.description,
        item_type=model.item_type,
        selected_techniques=model.selected_techniques or [],
        covered_by_test_cases=list(model.covered_by_test_cases or []),
    )


async def _resolve_internal_id(db: AsyncSession, requirement_id: str | None) -> tuple[str, str]:
    if not requirement_id:
        raise ValueError("requirement_id is required for persistence")

    model = await db.get(RequirementModel, requirement_id)
    if model is None:
        result = await db.execute(
            select(RequirementModel).where(RequirementModel.external_id == requirement_id)
        )
        model = result.scalar_one_or_none()
    if model is None:
        raise ValueError(f"Requirement {requirement_id} not found")

    return model.id, requirement_ref_id(model)


async def _clear_source(db: AsyncSession, internal_req_id: str, source_type: str) -> None:
    await db.execute(
        delete(TestSuiteModel).where(
            TestSuiteModel.requirement_id == internal_req_id,
            TestSuiteModel.source_type == source_type,
        )
    )
    if source_type in {"combined", "blackbox"}:
        await db.execute(
            delete(CoverageItemModel).where(CoverageItemModel.requirement_id == internal_req_id)
        )
    if source_type == "whitebox":
        await db.execute(
            delete(DesignArtifactModel).where(
                DesignArtifactModel.requirement_id == internal_req_id,
                DesignArtifactModel.artifact_type == "whitebox",
            )
        )


async def persist_suite(
    db: AsyncSession,
    *,
    requirement_id: str | None,
    suite: TestSuite,
    source_type: str,
    coverage_items: list[CoverageItem] | None = None,
) -> TestSuite:
    internal_id, requirement_ref = await _resolve_internal_id(db, requirement_id)
    await _clear_source(db, internal_id, source_type)

    suite_model = TestSuiteModel(
        id=suite.id,
        requirement_id=internal_id,
        name=suite.name,
        description=suite.description,
        source_type=source_type,
        optimization_applied=suite.optimization_applied,
    )
    db.add(suite_model)

    for case in suite.test_cases:
        db.add(_case_to_model(case, internal_id, requirement_ref, suite_model.id))

    if coverage_items:
        for item in coverage_items:
            db.add(_coverage_to_model(item, internal_id, requirement_ref))

    await db.commit()
    return suite


async def persist_whitebox(
    db: AsyncSession,
    *,
    requirement_id: str | None,
    suite_name: str,
    test_cases: list[TestCase],
    payload: dict[str, Any],
) -> None:
    internal_id, requirement_ref = await _resolve_internal_id(db, requirement_id)
    await _clear_source(db, internal_id, "whitebox")

    suite = TestSuite(
        id=f"wb-suite-{internal_id}",
        name=suite_name,
        description="Whitebox modeling output",
        test_cases=test_cases,
    )
    suite_model = TestSuiteModel(
        id=suite.id,
        requirement_id=internal_id,
        name=suite.name,
        description=suite.description,
        source_type="whitebox",
    )
    db.add(suite_model)
    for case in test_cases:
        db.add(_case_to_model(case, internal_id, requirement_ref, suite_model.id))

    db.add(
        DesignArtifactModel(
            requirement_id=internal_id,
            artifact_type="whitebox",
            payload=payload,
        )
    )
    await db.commit()


async def get_cases_for_requirement(
    db: AsyncSession,
    internal_req_id: str,
    source_type: str | None = None,
) -> list[TestCase]:
    stmt = select(TestCaseModel).where(TestCaseModel.requirement_id == internal_req_id)
    if source_type:
        stmt = stmt.join(TestSuiteModel, TestCaseModel.suite_id == TestSuiteModel.id).where(
            TestSuiteModel.source_type == source_type
        )
    result = await db.execute(stmt)
    return [_case_from_model(row) for row in result.scalars().all()]


async def get_coverage_for_requirement(db: AsyncSession, internal_req_id: str) -> list[CoverageItem]:
    result = await db.execute(
        select(CoverageItemModel).where(CoverageItemModel.requirement_id == internal_req_id)
    )
    return [_coverage_from_model(row) for row in result.scalars().all()]


async def get_suite_for_requirement(
    db: AsyncSession,
    internal_req_id: str,
    source_type: str,
) -> TestSuite | None:
    result = await db.execute(
        select(TestSuiteModel)
        .where(
            TestSuiteModel.requirement_id == internal_req_id,
            TestSuiteModel.source_type == source_type,
        )
        .order_by(TestSuiteModel.created_at.desc())
    )
    suite_model = result.scalars().first()
    if not suite_model:
        return None
    cases = await get_cases_for_requirement(db, internal_req_id, source_type)
    return TestSuite(
        id=suite_model.id,
        name=suite_model.name,
        description=suite_model.description,
        test_cases=cases,
        optimization_applied=suite_model.optimization_applied,
        created_at=suite_model.created_at.isoformat() if suite_model.created_at else None,
    )


async def load_review_bundles(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(select(RequirementModel).order_by(RequirementModel.created_at.asc()))
    bundles: list[dict[str, Any]] = []
    for req in result.scalars().all():
        ref = requirement_ref_id(req)
        suite = await get_suite_for_requirement(db, req.id, "combined")
        cases = suite.test_cases if suite else []
        if not cases:
            suite = await get_suite_for_requirement(db, req.id, "blackbox")
            cases = suite.test_cases if suite else []
        if not cases:
            continue
        coverage = await get_coverage_for_requirement(db, req.id)
        if not coverage:
            coverage = _coverage_from_cases(cases, ref)
        bundles.append(
            {
                "requirement_id": req.id,
                "external_id": req.external_id,
                "title": req.title,
                "requirement_ref": ref,
                "suite": suite,
                "test_cases": cases,
                "coverage_items": coverage,
            }
        )
    return bundles


def _coverage_from_cases(cases: list[TestCase], requirement_ref: str) -> list[CoverageItem]:
    coverage_map: dict[str, CoverageItem] = {}
    for test_case in cases:
        for coverage_id in test_case.coverage_items:
            existing = coverage_map.get(coverage_id)
            if existing:
                existing.covered_by_test_cases = list(
                    {*existing.covered_by_test_cases, test_case.id}
                )
                continue
            coverage_map[coverage_id] = CoverageItem(
                id=coverage_id,
                requirement_id=requirement_ref,
                description=coverage_id,
                item_type="state_transition"
                if test_case.technique == "StateTransition"
                else "blackbox",
                selected_techniques=[],
                covered_by_test_cases=[test_case.id],
            )
    return list(coverage_map.values())


async def save_review_bundle(
    db: AsyncSession,
    *,
    internal_req_id: str,
    test_cases: list[TestCase],
    coverage_items: list[CoverageItem],
) -> None:
    _, requirement_ref = await _resolve_internal_id(db, internal_req_id)
    suite = await get_suite_for_requirement(db, internal_req_id, "combined")
    if suite is None:
        suite = await get_suite_for_requirement(db, internal_req_id, "blackbox")
    if suite is None:
        return

    await db.execute(delete(TestCaseModel).where(TestCaseModel.suite_id == suite.id))
    for case in test_cases:
        db.add(_case_to_model(case, internal_req_id, requirement_ref, suite.id))

    await db.execute(delete(CoverageItemModel).where(CoverageItemModel.requirement_id == internal_req_id))
    for item in coverage_items:
        db.add(_coverage_to_model(item, internal_req_id, requirement_ref))

    await db.commit()
