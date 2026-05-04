"""ConditionAnnotation model — reviewer-added condition label for a building part.

Maps to: public.condition_annotations (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConditionAnnotation(Base):
    """Structured condition note tied to a passport field path, with optional photo evidence."""

    __tablename__ = "condition_annotations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    building_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE")
    )
    target_path: Mapped[str] = mapped_column(Text, nullable=False)
    condition_label: Mapped[str] = mapped_column(Text, nullable=False)
    salvage_label: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    photo_asset_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    actor_user_id: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
