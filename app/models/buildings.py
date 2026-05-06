"""Building model — global building identity record keyed by EHR code.

Maps to: public.buildings (doc 10)
"""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Index, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Building(Base, TimestampMixin):
    __tablename__ = "buildings"
    __table_args__ = (
        Index("idx_buildings_primary_ehr_code", "primary_ehr_code"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    country_code: Mapped[str] = mapped_column(Text, nullable=False, server_default="EE")
    primary_ehr_code: Mapped[str | None] = mapped_column(Text)
    normalized_address: Mapped[str | None] = mapped_column(Text)
    address_aliases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    municipality: Mapped[str | None] = mapped_column(Text)
    county: Mapped[str | None] = mapped_column(Text)
    source_identity_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
