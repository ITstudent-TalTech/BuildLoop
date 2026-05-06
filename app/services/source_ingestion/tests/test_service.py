"""Integration tests for SourceIngestionService.

Mocks EhrFetcher, dedup, storage, and AsyncSession — no live dependencies.

Acceptance criteria covered (doc 12 Agent 3):
  - Clean fetch persists a source_documents row with checksum, storage_bucket,
    storage_path, fetched_at, parser_status='fetched'.
  - Fetch failure persists a source_documents row with parser_status='fetch_failed'
    and the error captured in fetch_metadata. Same input on retry produces the
    same failure shape (deterministic error path).
  - Duplicate fetch (same checksum) returns the existing source_document_id
    without re-uploading. Only one Storage upload occurs.
  - project_not_found returns status='project_not_found'.
  - project_not_resolved returns status='project_not_resolved'.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.source_ingestion.service import SourceIngestionService
from app.services.source_ingestion.types import EhrFetchResult

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_ehr.pdf"
SAMPLE_BYTES = FIXTURE_PDF.read_bytes()
SAMPLE_CHECKSUM = "a" * 64  # placeholder; real checksum computed by EhrFetcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ok_fetch_result(content: bytes = SAMPLE_BYTES) -> EhrFetchResult:
    import hashlib
    checksum = hashlib.sha256(content).hexdigest()
    return EhrFetchResult(
        ok=True,
        content=content,
        checksum=checksum,
        source_uri="https://test-ehr.example.com/api/document/v1/pdf/document/file/101035685",
        error=None,
        ssl_fallback_used=False,
        status_code=200,
        fetch_metadata={"url": "...", "http_code": 200, "bytes": len(content)},
    )


def _make_failed_fetch_result(error: str = "ehr_http_500") -> EhrFetchResult:
    return EhrFetchResult(
        ok=False,
        content=None,
        checksum=None,
        source_uri="https://test-ehr.example.com/api/document/v1/pdf/document/file/101035685",
        error=error,
        ssl_fallback_used=False,
        status_code=500,
        fetch_metadata={"url": "...", "http_code": 500, "response_preview": "error"},
    )


def _make_mock_fetcher(result: EhrFetchResult) -> Any:
    from app.services.source_ingestion.ehr_fetcher import EhrFetcher
    fetcher = MagicMock(spec=EhrFetcher)
    fetcher.fetch_pdf = AsyncMock(return_value=result)
    return fetcher


def _make_project(building_id: UUID | None = None) -> Any:
    from app.models.projects import Project
    project = MagicMock(spec=Project)
    project.id = uuid4()
    project.building_id = building_id
    return project


def _make_source_doc(doc_id: UUID) -> Any:
    from app.models.source_documents import SourceDocument
    doc = MagicMock(spec=SourceDocument)
    doc.id = doc_id
    doc.checksum = "existing-checksum"
    doc.building_id = uuid4()
    return doc


def _make_mock_db(
    project: Any,
    dedup_result: Any = None,
) -> AsyncMock:
    """Build a mock AsyncSession for service tests."""
    mock_db = AsyncMock()

    async def _get(model_class: Any, pk: Any, *args: Any, **kwargs: Any) -> Any:
        from app.models.projects import Project
        if model_class is Project:
            return project
        return None

    mock_db.get.side_effect = _get
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()

    # Default execute() for list_for_project and dedup
    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = dedup_result
    mock_scalars_result = MagicMock()
    mock_scalars_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_scalar_result

    return mock_db


# ---------------------------------------------------------------------------
# Acceptance criterion 1: clean fetch persists row + uploads to storage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clean_fetch_persists_row_and_uploads() -> None:
    """
    Acceptance: source document is stored with metadata.
    A successful fetch → source_documents row with checksum, storage_bucket,
    storage_path, fetched_at, parser_status='fetched'.
    """
    building_id = uuid4()
    project = _make_project(building_id=building_id)
    mock_db = _make_mock_db(project, dedup_result=None)
    fetch_result = _make_ok_fetch_result()

    upload_calls: list[dict] = []

    async def _fake_upload(building_id: UUID, source_document_id: UUID, content: bytes) -> tuple[str, str]:
        upload_calls.append({"building_id": building_id, "source_document_id": source_document_id})
        return "source-documents", f"{building_id}/{source_document_id}.pdf"

    fetcher = _make_mock_fetcher(fetch_result)

    with patch("app.services.source_ingestion.service.storage_module.upload_ehr_pdf", side_effect=_fake_upload):
        svc = SourceIngestionService(fetcher=fetcher)
        result = await svc.fetch_for_project(uuid4(), "101035685", mock_db)

    assert result.status == "ok"
    assert result.fetch_status == "ok"
    assert result.source_document_id is not None
    assert result.source_type == "ehr_pdf"

    # Verify db.add was called with a SourceDocument
    added_types = [type(c.args[0]).__name__ for c in mock_db.add.call_args_list]
    assert "SourceDocument" in added_types

    # Verify Storage upload happened
    assert len(upload_calls) == 1
    assert upload_calls[0]["building_id"] == building_id

    # Verify the persisted SourceDocument has the expected fields
    from app.models.source_documents import SourceDocument
    added_docs = [c.args[0] for c in mock_db.add.call_args_list if isinstance(c.args[0], SourceDocument)]
    assert len(added_docs) == 1
    doc = added_docs[0]
    assert doc.checksum == fetch_result.checksum
    assert doc.storage_bucket == "source-documents"
    assert doc.storage_path is not None
    assert doc.fetched_at is not None
    assert doc.parser_status == "fetched"


# ---------------------------------------------------------------------------
# Acceptance criterion 2: fetch failure persists fetch_failed row
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_failure_persists_fetch_failed_row() -> None:
    """
    Acceptance: failures are reproducible and diagnosable.
    EHR 500 → source_documents row with parser_status='fetch_failed',
    error in fetch_metadata.
    """
    building_id = uuid4()
    project = _make_project(building_id=building_id)
    mock_db = _make_mock_db(project)
    fetch_result = _make_failed_fetch_result("ehr_http_500")

    fetcher = _make_mock_fetcher(fetch_result)

    svc = SourceIngestionService(fetcher=fetcher)
    result = await svc.fetch_for_project(uuid4(), "101035685", mock_db)

    assert result.status == "fetch_failed"
    assert result.fetch_status == "failed"
    assert result.error == "ehr_http_500"

    from app.models.source_documents import SourceDocument
    added_docs = [c.args[0] for c in mock_db.add.call_args_list if isinstance(c.args[0], SourceDocument)]
    assert len(added_docs) == 1
    doc = added_docs[0]
    assert doc.parser_status == "fetch_failed"
    assert "error" in doc.fetch_metadata
    assert doc.fetch_metadata["error"] == "ehr_http_500"


@pytest.mark.asyncio
async def test_fetch_failure_is_deterministic() -> None:
    """Same failed fetch called twice produces the same failure shape."""
    building_id = uuid4()
    project = _make_project(building_id=building_id)

    for _ in range(2):
        mock_db = _make_mock_db(project)
        fetch_result = _make_failed_fetch_result("ehr_http_500")
        fetcher = _make_mock_fetcher(fetch_result)

        svc = SourceIngestionService(fetcher=fetcher)
        result = await svc.fetch_for_project(uuid4(), "101035685", mock_db)

        assert result.status == "fetch_failed"
        assert result.error == "ehr_http_500"


# ---------------------------------------------------------------------------
# Acceptance criterion 3: idempotent dedup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_fetch_returns_existing_without_reuploading() -> None:
    """
    Acceptance: ingestion is idempotent for same source version.
    Same checksum → returns existing source_document_id, no Storage upload.
    """
    building_id = uuid4()
    existing_id = uuid4()
    project = _make_project(building_id=building_id)

    fetch_result = _make_ok_fetch_result()
    existing_doc = _make_source_doc(existing_id)

    # make dedup return the existing doc
    mock_db = _make_mock_db(project, dedup_result=existing_doc)

    upload_calls: list = []

    async def _fake_upload(building_id: UUID, source_document_id: UUID, content: bytes) -> tuple[str, str]:
        upload_calls.append(1)
        return "source-documents", f"{building_id}/{source_document_id}.pdf"

    fetcher = _make_mock_fetcher(fetch_result)

    with patch("app.services.source_ingestion.service.storage_module.upload_ehr_pdf", side_effect=_fake_upload):
        svc = SourceIngestionService(fetcher=fetcher)
        result = await svc.fetch_for_project(uuid4(), "101035685", mock_db)

    assert result.status == "ok"
    assert result.fetch_status == "deduped"
    assert result.source_document_id == existing_id

    # No Storage upload should have happened
    assert len(upload_calls) == 0


# ---------------------------------------------------------------------------
# Error shapes: project_not_found, project_not_resolved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_project_not_found_returns_project_not_found_status() -> None:
    """Missing project → status='project_not_found'."""
    mock_db = AsyncMock()
    mock_db.get.return_value = None
    mock_db.commit = AsyncMock()

    svc = SourceIngestionService()
    result = await svc.fetch_for_project(uuid4(), "101035685", mock_db)

    assert result.status == "project_not_found"
    assert result.source_document_id is None


@pytest.mark.asyncio
async def test_project_not_resolved_returns_project_not_resolved_status() -> None:
    """Project exists but building_id is None → status='project_not_resolved'."""
    project = _make_project(building_id=None)
    mock_db = _make_mock_db(project)

    svc = SourceIngestionService()
    result = await svc.fetch_for_project(uuid4(), "101035685", mock_db)

    assert result.status == "project_not_resolved"
    assert result.source_document_id is None


# ---------------------------------------------------------------------------
# list_for_project
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_for_project_returns_empty_list_when_no_docs() -> None:
    mock_db = AsyncMock()
    scalars_mock = MagicMock()
    scalars_mock.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = scalars_mock

    svc = SourceIngestionService()
    result = await svc.list_for_project(uuid4(), mock_db)
    assert result == []


@pytest.mark.asyncio
async def test_list_for_project_returns_summaries() -> None:
    from app.models.source_documents import SourceDocument
    from datetime import datetime, timezone

    doc = MagicMock(spec=SourceDocument)
    doc.id = uuid4()
    doc.source_type = "ehr_pdf"
    doc.source_uri = "https://example.com/pdf/123"
    doc.mime_type = "application/pdf"
    doc.checksum = "abc123"
    doc.fetched_at = datetime.now(tz=timezone.utc)
    doc.parser_status = "fetched"
    doc.storage_bucket = "source-documents"
    doc.storage_path = "building-id/doc-id.pdf"

    mock_db = AsyncMock()
    scalars_mock = MagicMock()
    scalars_mock.scalars.return_value.all.return_value = [doc]
    mock_db.execute.return_value = scalars_mock

    svc = SourceIngestionService()
    results = await svc.list_for_project(uuid4(), mock_db)

    assert len(results) == 1
    summary = results[0]
    assert summary.source_document_id == doc.id
    assert summary.source_type == "ehr_pdf"
    assert summary.checksum == "abc123"
    assert summary.parser_status == "fetched"
