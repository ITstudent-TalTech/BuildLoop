"""Resolver run and candidate models — address resolution audit trail.

Maps to: public.address_resolution_runs and
         public.address_resolution_candidates (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResolverRun(Base):
    """One attempt to resolve an intake request to a canonical EHR code."""

    __tablename__ = "address_resolution_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    intake_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("intake_requests.id", ondelete="CASCADE")
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    resolver_version: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_ehr_code: Mapped[str | None] = mapped_column(Text)
    normalized_address: Mapped[str | None] = mapped_column(Text)
    address_aliases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reason: Mapped[str | None] = mapped_column(Text)
    query_variants: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ResolverCandidate(Base):
    """One EHR candidate returned within a resolver run."""

    __tablename__ = "address_resolution_candidates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    resolution_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("address_resolution_runs.id", ondelete="CASCADE")
    )
    ehr_code: Mapped[str | None] = mapped_column(Text)
    normalized_address: Mapped[str | None] = mapped_column(Text)
    address_aliases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    object_types: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    matched_query_variants: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    match_reasons: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    primary_candidate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    raw_candidate: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
