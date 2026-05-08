"""Pydantic request/response schemas for passport draft endpoints.

Matches doc 11 § 4 (passport draft generation + retrieval) and the
FieldValue<T> + PassportDraft types in web/lib/api/types.ts.

The POST /v1/projects/{id}/passport-drafts response uses
PassportDraftGenerateResponse.

The GET /v1/projects/{id}/passport-draft response returns the full
payload_json dict (merged with ORM metadata), validated as
PassportDraftGetResponse.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class FieldSource(BaseModel):
    """Provenance pointer embedded inside each FieldValue.

    Matches web/lib/api/types.ts FieldSource.
    """

    document_id: str
    page: int | None = None
    label: str


class FieldValue(BaseModel):
    """Single-field value with confidence and source provenance.

    Matches web/lib/api/types.ts FieldValue<T>.  The value type is Any
    because the generic parameter varies per field (string, number, list…).
    """

    value: Any
    unit: str | None = None
    confidence: Literal["high", "medium", "low"]
    source: FieldSource | None = None
    last_updated: str | None = None


class PassportDraftGenerateResponse(BaseModel):
    """POST /v1/projects/{project_id}/passport-drafts response.

    Matches web/lib/api/types.ts PassportDraftResponse.
    """

    status: Literal["ok"] = "ok"
    passport_draft_id: UUID
    schema_version: str
    schema_completeness_score: float
    confidence_score: float


class PassportDraftGetResponse(BaseModel):
    """GET /v1/projects/{project_id}/passport-draft response.

    Wraps the payload_json with the ORM-level metadata fields so the
    frontend receives the full PassportDraft shape from types.ts.
    """

    passport_draft_id: UUID
    building_id: UUID | None
    project_id: UUID | None
    schema_version: str
    status: str
    generated_at: str
    # Content sections — kept as Any to avoid redefining the full schema
    # in Python; projection.py guarantees the FieldValue<T> shape.
    identity: dict[str, Any]
    building_profile: dict[str, Any]
    structural_systems: dict[str, Any]
    technical_systems: dict[str, Any]
    location: dict[str, Any]
    building_parts: dict[str, Any]
    quality: dict[str, Any]
