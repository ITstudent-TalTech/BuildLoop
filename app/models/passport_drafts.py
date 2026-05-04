"""PassportDraft model — system-generated passport draft before review.

Maps to: public.passport_drafts (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PassportDraft(Base):
    """Versioned snapshot of a projected passport, pending professional review."""

    __tablename__ = "passport_drafts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    building_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE")
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="draft_system_generated"
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    schema_completeness_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
