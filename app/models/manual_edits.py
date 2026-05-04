"""ManualEdit model — audit record of every human override on a passport draft.

Maps to: public.manual_edits (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ManualEdit(Base):
    """Immutable audit entry for one field change applied during passport review."""

    __tablename__ = "manual_edits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    building_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE")
    )
    passport_draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("passport_drafts.id", ondelete="CASCADE")
    )
    target_field_path: Mapped[str] = mapped_column(Text, nullable=False)
    old_value_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_value_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    edit_type: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    actor_user_id: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
