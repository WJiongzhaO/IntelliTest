"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RequirementModel(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    input_fields: Mapped[list] = mapped_column(JSON, default=list)
    data_ranges: Mapped[list] = mapped_column(JSON, default=list)
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    expected_actions: Mapped[list] = mapped_column(JSON, default=list)
    is_structured: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_impact: Mapped[int] = mapped_column(Integer, nullable=True)
    risk_likelihood: Mapped[int] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=True)
    risk_impact_rationale: Mapped[str] = mapped_column(Text, nullable=True)
    risk_likelihood_rationale: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    test_suites: Mapped[list["TestSuiteModel"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    test_cases: Mapped[list["TestCaseModel"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    coverage_items: Mapped[list["CoverageItemModel"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
    design_artifacts: Mapped[list["DesignArtifactModel"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )


class TestSuiteModel(Base):
    __tablename__ = "test_suites"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    requirement_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    optimization_applied: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    requirement: Mapped["RequirementModel"] = relationship(back_populates="test_suites")
    test_cases: Mapped[list["TestCaseModel"]] = relationship(
        back_populates="suite", cascade="all, delete-orphan"
    )


class TestCaseModel(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    requirement_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    suite_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=True
    )
    requirement_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    precondition: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_steps: Mapped[list] = mapped_column(JSON, default=list)
    test_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    technique: Mapped[str | None] = mapped_column(String(32), nullable=True)
    priority: Mapped[str] = mapped_column(String(16), default="Medium")
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_items: Mapped[list] = mapped_column(JSON, default=list)
    modified_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    requirement: Mapped["RequirementModel"] = relationship(back_populates="test_cases")
    suite: Mapped["TestSuiteModel | None"] = relationship(back_populates="test_cases")


class CoverageItemModel(Base):
    __tablename__ = "coverage_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    requirement_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    requirement_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(String(64), nullable=False)
    selected_techniques: Mapped[list] = mapped_column(JSON, default=list)
    covered_by_test_cases: Mapped[list] = mapped_column(JSON, default=list)

    requirement: Mapped["RequirementModel"] = relationship(back_populates="coverage_items")


class DesignArtifactModel(Base):
    __tablename__ = "design_artifacts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    requirement_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    artifact_type: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    requirement: Mapped["RequirementModel"] = relationship(back_populates="design_artifacts")
