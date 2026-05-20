"""API router aggregating all feature sub-routers."""

from fastapi import APIRouter

from app.api.blackbox import router as blackbox_router
from app.api.oracle import router as oracle_router
from app.api.requirements import router as requirements_router
from app.api.risk import router as risk_router
from app.api.suites import router as suites_router
from app.api.test_design import router as test_design_router
from app.api.whitebox import router as whitebox_router

api_router = APIRouter()

api_router.include_router(requirements_router)
api_router.include_router(risk_router)
api_router.include_router(suites_router)
api_router.include_router(blackbox_router)
api_router.include_router(whitebox_router, prefix="/whitebox", tags=["whitebox"])
api_router.include_router(oracle_router, prefix="/oracle", tags=["oracle"])
api_router.include_router(test_design_router, prefix="/test-design", tags=["test-design"])


@api_router.get("/ping")
async def ping():
    return {"message": "IntelliTest API v0.1.0"}
