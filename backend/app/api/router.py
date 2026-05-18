"""API router aggregating all feature sub-routers."""

from fastapi import APIRouter

from app.api.blackbox import router as blackbox_router

api_router = APIRouter()

# Include black-box testing routes
api_router.include_router(blackbox_router)

# TODO: Import and include sub-routers as features are implemented
# from app.api.requirements import router as requirements_router
# from app.api.risk import router as risk_router

# Placeholder health-check at the router level
@api_router.get("/ping")
async def ping():
    return {"message": "IntelliTest API v0.1.0"}
