"""Internal type definitions for the passport_engine service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class ProjectionResult:
    """Returned by PassportEngine.generate_draft().

    Carries both the summary metadata (for lightweight responses) and the
    full payload (so callers like the pipeline route can avoid a second
    DB round-trip).
    """

    passport_draft_id: UUID
    schema_version: str
    schema_completeness_score: float
    confidence_score: float
    # Full draft context — populated from the upserted draft row
    building_id: UUID | None
    project_id: UUID
    status: str
    generated_at: str  # ISO 8601
    payload_json: dict[str, Any] = field(default_factory=dict)
