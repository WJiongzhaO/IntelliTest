"""FR 5.0 test oracle API routes."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engines.oracle_synthesizer.synthesizer import DefaultOracleSynthesizer
from app.exceptions import OracleSynthesisError
from app.models.oracle import OracleResult
from app.models.requirement import StructuredRequirement
from app.models.test_case import TestCase, TestSuite
from app.repositories.memory_store import store

router = APIRouter()


class OracleSynthesizeRequest(BaseModel):
    requirement: StructuredRequirement
    test_cases: list[TestCase] = Field(default_factory=list)
    test_case_ids: list[str] = Field(default_factory=list)
    use_llm: bool = True


class OracleSynthesizeResponse(BaseModel):
    oracles: list[OracleResult]


class OracleValidateRequest(BaseModel):
    requirement: StructuredRequirement
    test_case: TestCase
    expected_result: str


class OracleReviewRequest(BaseModel):
    action: Literal["confirm", "reject"]
    edited_expected_result: Optional[str] = None
    sync_test_case: bool = True


class OracleBatchSuiteRequest(BaseModel):
    requirement: StructuredRequirement
    suite: TestSuite
    use_llm: bool = True


@router.post("/synthesize", response_model=OracleSynthesizeResponse)
def synthesize_oracles(body: OracleSynthesizeRequest) -> OracleSynthesizeResponse:
    synthesizer = DefaultOracleSynthesizer()
    targets = list(body.test_cases)

    if body.test_case_ids and not targets:
        raise HTTPException(
            status_code=400,
            detail="test_case_ids lookup not implemented; pass test_cases inline",
        )

    results: list[OracleResult] = []
    for case in targets:
        try:
            oracle = synthesizer.synthesize(
                body.requirement,
                case,
                use_llm=body.use_llm,
            )
        except OracleSynthesisError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        store.oracles[oracle.id] = oracle
        results.append(oracle)

    return OracleSynthesizeResponse(oracles=results)


@router.post("/validate", response_model=OracleResult)
def validate_oracle(body: OracleValidateRequest) -> OracleResult:
    synthesizer = DefaultOracleSynthesizer()
    oracle = synthesizer.validate_only(
        body.requirement,
        body.test_case,
        body.expected_result,
    )
    store.oracles[oracle.id] = oracle
    return oracle


@router.put("/{oracle_id}/review", response_model=OracleResult)
def review_oracle(oracle_id: str, body: OracleReviewRequest) -> OracleResult:
    oracle = store.oracles.get(oracle_id)
    if not oracle:
        raise HTTPException(status_code=404, detail="Oracle not found")

    status = "confirmed" if body.action == "confirm" else "rejected"
    expected = body.edited_expected_result or oracle.expected_result
    updated = oracle.model_copy(
        update={
            "status": status,
            "expected_result": expected,
            "modified_by_user": True,
            "revision": oracle.revision + 1,
        }
    )
    store.oracles[oracle_id] = updated

    if body.sync_test_case and body.action == "confirm":
        cached = store.test_cases.get(updated.test_case_id)
        if isinstance(cached, TestCase):
            store.test_cases[updated.test_case_id] = cached.model_copy(
                update={
                    "expected_result": expected,
                    "modified_by_user": True,
                }
            )

    return updated


@router.post("/batch-from-suite", response_model=OracleSynthesizeResponse)
def batch_from_suite(body: OracleBatchSuiteRequest) -> OracleSynthesizeResponse:
    synthesizer = DefaultOracleSynthesizer()
    results: list[OracleResult] = []

    for case in body.suite.test_cases:
        if case.expected_result:
            continue
        try:
            oracle = synthesizer.synthesize(
                body.requirement,
                case,
                use_llm=body.use_llm,
            )
        except OracleSynthesisError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        store.oracles[oracle.id] = oracle
        results.append(oracle)

    return OracleSynthesizeResponse(oracles=results)
