"""Passport engine test configuration.

Env vars set before any app module is imported so Settings initialises cleanly.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/buildloop_test")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

from app.models.observations import Observation  # noqa: E402  (after env vars)
from app.models.source_documents import SourceDocument  # noqa: E402

GOLDEN_FILE_PATH = (
    Path(__file__).parent.parent.parent
    / "source_parsing" / "tests" / "fixtures" / "expected"
    / "lai_1_observations.json"
)

_FIXED_NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)
_FIXED_DOC_ID: UUID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def make_obs(
    namespace: str,
    key: str,
    value: Any,
    *,
    unit: str | None = None,
    confidence_label: str = "high",
    page_number: int | None = 1,
    relevance_class: str = "unclassified",
    created_at: datetime | None = None,
    source_document_id: UUID | None = None,
) -> Any:
    """Create a MagicMock Observation suitable for unit tests."""
    obs = MagicMock(spec=Observation)
    obs.id = uuid4()
    obs.building_id = None
    obs.project_id = None
    obs.extraction_run_id = None
    obs.source_document_id = source_document_id or _FIXED_DOC_ID
    obs.namespace = namespace
    obs.key = key
    obs.section = namespace
    obs.value_json = value
    obs.unit = unit
    obs.relevance_class = relevance_class
    obs.confidence_score = None
    obs.confidence_label = confidence_label
    obs.evidence_text = None
    obs.page_number = page_number
    obs.source_locator = None
    obs.created_at = created_at or _FIXED_NOW
    return obs


def make_source_doc(doc_id: UUID | None = None) -> Any:
    """Create a MagicMock SourceDocument for provenance population."""
    doc = MagicMock(spec=SourceDocument)
    doc.id = doc_id or _FIXED_DOC_ID
    doc.building_id = None
    doc.project_id = None
    doc.source_type = "ehr_pdf"
    doc.source_uri = None
    doc.mime_type = "application/pdf"
    doc.checksum = None
    doc.fetched_at = None
    doc.parser_status = "parsed"
    doc.storage_bucket = None
    doc.storage_path = None
    return doc
