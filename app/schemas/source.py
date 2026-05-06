"""Pydantic request/response schemas for the /v1/projects/{id}/sources endpoints.

All shapes match /web/lib/api/types.ts SourceFetchResponse and SourceDocument exactly.

Note: web/lib/api/types.ts defines ApiStatus = "ok" (only). The fetch endpoint
can return status values beyond "ok" (e.g. "fetch_failed", "project_not_resolved")
as specified in doc 11. This is intentional — the frontend schema is narrower
than the server schema because the frontend currently only renders the happy path.
Track 3 (frontend integration) should widen ApiStatus or handle non-ok branches.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class SourceFetchRequest(BaseModel):
    """POST /v1/projects/{project_id}/sources/fetch request body."""

    ehr_code: str


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class SourceFetchResponse(BaseModel):
    """POST /v1/projects/{project_id}/sources/fetch response.

    Matches web/lib/api/types.ts SourceFetchResponse.
    status: 'ok' | 'fetch_failed' | 'project_not_found' | 'project_not_resolved'
    fetch_status: 'ok' | 'deduped' | 'failed'
    """

    status: str
    source_document_id: UUID | None
    source_type: str
    fetch_status: str
    error: str | None = None


class SourceDocumentSummaryResponse(BaseModel):
    """One entry in the GET /v1/projects/{project_id}/sources list response.

    Matches web/lib/api/types.ts SourceDocument.
    """

    source_document_id: UUID
    source_type: str
    source_uri: str | None
    mime_type: str | None
    checksum: str | None
    fetched_at: datetime | None
    parser_status: str | None
    storage_bucket: str | None
    storage_path: str | None
