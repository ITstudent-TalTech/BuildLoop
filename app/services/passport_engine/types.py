"""Internal type definitions for the passport_engine service."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class ProjectionResult:
    """Returned by PassportEngine.generate_draft()."""

    passport_draft_id: UUID
    schema_version: str
    schema_completeness_score: float
    confidence_score: float
