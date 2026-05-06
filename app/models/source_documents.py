"""SourceDocument model — metadata for a fetched source PDF or artifact.

Maps to: public.source_documents (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SourceDocument(Base):
    """Metadata record for one fetched source document; binary stored in Supabase Storage."""

    __tablename__ = "source_documents"
    __table_args__ = (
        Index("idx_source_documents_building_id", "building_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    building_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE")
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_uri: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parser_status: Mapped[str | None] = mapped_column(Text)
    storage_bucket: Mapped[str | None] = mapped_column(Text)
    storage_path: Mapped[str | None] = mapped_column(Text)
    fetch_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
