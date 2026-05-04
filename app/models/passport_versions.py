"""PassportVersion model — immutable published version of a passport draft.

Maps to: public.passport_versions (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PassportVersion(Base):
    """Immutable published passport. Each publication creates a new version row."""

    __tablename__ = "passport_versions"
    __table_args__ = (
        UniqueConstraint("passport_draft_id", "version_number", name="idx_passport_versions_unique"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    passport_draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("passport_drafts.id", ondelete="CASCADE")
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    pdf_storage_bucket: Mapped[str | None] = mapped_column(Text)
    pdf_storage_path: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_by: Mapped[UUID | None]
