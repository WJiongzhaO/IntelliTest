"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.database import engine
from app.models.db_models import Base


def _requirements_has_title_column(sync_conn) -> bool:
    inspector = inspect(sync_conn)
    if "requirements" not in inspector.get_table_names():
        return True
    return any(column["name"] == "title" for column in inspector.get_columns("requirements"))


def _requirements_has_external_id_column(sync_conn) -> bool:
    inspector = inspect(sync_conn)
    if "requirements" not in inspector.get_table_names():
        return True
    return any(column["name"] == "external_id" for column in inspector.get_columns("requirements"))


def _requirements_has_module_column(sync_conn) -> bool:
    inspector = inspect(sync_conn)
    if "requirements" not in inspector.get_table_names():
        return True
    return any(column["name"] == "module" for column in inspector.get_columns("requirements"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        has_title = await conn.run_sync(_requirements_has_title_column)
        if not has_title:
            await conn.execute(text("ALTER TABLE requirements ADD COLUMN title VARCHAR(255)"))
        has_external_id = await conn.run_sync(_requirements_has_external_id_column)
        if not has_external_id:
            await conn.execute(text("ALTER TABLE requirements ADD COLUMN external_id VARCHAR(64)"))
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_requirements_external_id "
                    "ON requirements (external_id) WHERE external_id IS NOT NULL"
                )
            )
        has_module = await conn.run_sync(_requirements_has_module_column)
        if not has_module:
            await conn.execute(text("ALTER TABLE requirements ADD COLUMN module VARCHAR(128)"))
    yield
    await engine.dispose()


app = FastAPI(
    title="IntelliTest API",
    description="AI-Driven AutoTestDesign Tool",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
