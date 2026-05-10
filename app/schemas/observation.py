"""Pydantic response schemas for the observations endpoints.

Matches doc 11 § 3 — POST /v1/source-documents/{id}/parse
and GET /v1/projects/{id}/observations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ParseResponse(BaseModel):
    """POST /v1/source-documents/{source_document_id}/parse response.

    Matches doc 11 § 3 parse response shape.
    status: 'ok' | 'source_not_found' | 'wrong_status' | 'parse_failed'
    """

    status: str
    extraction_run_id: UUID | None = None
    observation_count: int = 0
    error: str | None = None


class ObservationSummary(BaseModel):
    """One entry in GET /v1/projects/{project_id}/observations response.

    Includes all fields the frontend will need per doc 11 § 3.
    """

    observation_id: UUID
    building_id: UUID | None
    project_id: UUID | None
    source_document_id: UUID | None
    extraction_run_id: UUID | None
    namespace: str
    key: str
    section: str
    value_json: Any
    unit: str | None
    relevance_class: str
    confidence_score: float | None
    confidence_label: str | None
    evidence_text: str | None
    page_number: int | None
    source_locator: str | None
    created_at: datetime
