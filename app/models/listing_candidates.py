"""ListingCandidate model — future-facing derived listing object from a passport.

Maps to: public.listing_candidates (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ListingCandidate(Base):
    """Derived marketplace listing candidate; not a core passport module concern."""

    __tablename__ = "listing_candidates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    building_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE")
    )
    source_passport_draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("passport_drafts.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="derived")
    listing_payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
