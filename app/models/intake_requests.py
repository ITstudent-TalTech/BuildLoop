"""IntakeRequest model — raw address submission from the user.

Maps to: public.intake_requests (doc 10)
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IntakeRequest(Base):
    __tablename__ = "intake_requests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    raw_address_input: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_input: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    country_code: Mapped[str] = mapped_column(Text, nullable=False, server_default="EE")
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="received")
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
