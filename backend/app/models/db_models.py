"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RequirementModel(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    input_fields: Mapped[list | None] = mapped_column(JSON, default=list)
    data_ranges: Mapped[list | None] = mapped_column(JSON, default=list)
    conditions: Mapped[list | None] = mapped_column(JSON, default=list)
    expected_actions: Mapped[list | None] = mapped_column(JSON, default=list)
    is_structured: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_impact: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_likelihood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_impact_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_likelihood_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
