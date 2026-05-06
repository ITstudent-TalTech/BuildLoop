"""Internal type definitions for the source_ingestion service.

These types are NOT the API layer — they are service-internal.
Pydantic API response shapes live in app/schemas/source.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class EhrFetchResult:
    """Result of one EHR PDF HTTP fetch attempt."""

    ok: bool
    content: bytes | None
    checksum: str | None
    """SHA-256 hex digest of content, or None if fetch failed."""

    source_uri: str
    """The URL that was requested."""

    error: str | None
    ssl_fallback_used: bool
    status_code: int | None
    fetch_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchResult:
    """The final result returned by SourceIngestionService to the API layer."""

    status: str
    """'ok' | 'fetch_failed' | 'project_not_found' | 'project_not_resolved'"""

    source_document_id: UUID | None
    source_type: str
    fetch_status: str
    """'ok' | 'deduped' | 'failed'"""

    error: str | None = None


@dataclass
class SourceDocumentSummary:
    """Summary of a persisted source_documents row returned by list_for_project."""

    source_document_id: UUID
    source_type: str
    source_uri: str | None
    mime_type: str | None
    checksum: str | None
    fetched_at: datetime | None
    parser_status: str | None
    storage_bucket: str | None
    storage_path: str | None
