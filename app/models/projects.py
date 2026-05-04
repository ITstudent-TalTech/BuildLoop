"""Project model — a user session targeting a specific building.

Maps to: public.projects (doc 10)
"""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    building_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="SET NULL")
    )
    owner_user_id: Mapped[UUID | None]
    title: Mapped[str | None] = mapped_column(Text)
    raw_input_address: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft")
