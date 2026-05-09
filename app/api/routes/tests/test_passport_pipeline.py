"""Tests for POST /v1/projects/{project_id}/passport-pipeline.

Unit tests mock all three services; each verifies one orchestration concern.
Integration test (test_pipeline_integration_against_lai_1) uses real services
with mocked I/O boundaries (EHR HTTP fetch + Supabase Storage).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.extraction_runs import ExtractionRun
from app.models.observations import Observation
from app.models.passport_drafts import PassportDraft
from app.models.projects import Project
from app.models.source_documents import SourceDocument
from app.services.passport_engine.types import ProjectionResult
from app.services.source_ingestion.types import FetchResult
from app.services.source_parsing.types import ParseResult

_FIXTURE_PDF = (
    Path(__file__).parent.parent.parent.parent
    / "services/source_parsing/tests/fixtures/pdfs/lai_1_101035685.pdf"
)


# ---------------------------------------------------------------------------
# Test client helper
# ---------------------------------------------------------------------------


def _mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    return db


async def _make_client(app: Any, db: AsyncMock) -> AsyncClient:
    from app.db.session import get_session

    async def override() -> Any:
        yield db

    app.dependency_overrides[get_session] = override
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


# ---------------------------------------------------------------------------
# Unit: happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_happy_path() -> None:
    """All three stages succeed; response has the full success shape."""
    import os

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/fake")
    os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

    from app.main import app

    project_id = uuid4()
    source_doc_id = uuid4()
    run_id = uuid4()
    draft_id = uuid4()

    mock_fetch = FetchResult(
        status="ok", source_document_id=source_doc_id,
        source_type="ehr_pdf", fetch_status="ok",
    )
    mock_parse = ParseResult(status="ok", extraction_run_id=run_id, observation_count=31)
    mock_proj = ProjectionResult(
        passport_draft_id=draft_id,
        schema_version="buildloop.passport.mvp.v1",
        schema_completeness_score=81.6,
        confidence_score=95.0,
        building_id=uuid4(),
        project_id=project_id,
        status="draft_system_generated",
        generated_at="2026-05-09T10:00:00+00:00",
        payload_json={
            "identity": {"ehr_code": {"value": "101035685", "confidence": "high", "source": None, "last_updated": None}},
            "building_profile": {}, "structural_systems": {}, "technical_systems": {},
            "location": {}, "building_parts": {},
            "quality": {"schema_completeness_score": 81.6, "confidence_score": 95.0,
                        "confidence_label": "high", "section_breakdown": {}, "missing_fields": []},
        },
    )

    db = _mock_db()
    client = await _make_client(app, db)

    try:
        with patch(
            "app.api.routes.passport_pipeline.SourceIngestionService.fetch_for_project",
            new_callable=AsyncMock, return_value=mock_fetch,
        ), patch(
            "app.api.routes.passport_pipeline.SourceParsingService.parse_source_document",
            new_callable=AsyncMock, return_value=mock_parse,
        ), patch(
            "app.api.routes.passport_pipeline.PassportEngine.generate_draft",
            new_callable=AsyncMock, return_value=mock_proj,
        ):
            async with client as c:
                resp = await c.post(
                    f"/v1/projects/{project_id}/passport-pipeline",
                    json={"ehr_code": "101035685"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["source_document_id"] == str(source_doc_id)
    assert body["extraction_run_id"] == str(run_id)
    assert body["passport_draft_id"] == str(draft_id)
    assert body["schema_version"] == "buildloop.passport.mvp.v1"
    assert body["schema_completeness_score"] == 81.6
    assert body["confidence_score"] == 95.0
    assert body["fetch_status"] == "ok"
    assert body["observation_count"] == 31
    assert body["draft"] is not None
    assert body["draft"]["identity"]["ehr_code"]["value"] == "101035685"


# ---------------------------------------------------------------------------
# Unit: short-circuit on fetch failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_short_circuits_on_fetch_failure() -> None:
    """Fetch failure → stage='fetch'; parse and project services not called."""
    import os

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/fake")
    os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

    from app.main import app

    project_id = uuid4()
    source_doc_id = uuid4()

    mock_fetch = FetchResult(
        status="fetch_failed",
        source_document_id=source_doc_id,
        source_type="ehr_pdf",
        fetch_status="failed",
        error="ehr_http_500: upstream returned 500",
    )

    db = _mock_db()
    client = await _make_client(app, db)

    try:
        with patch(
            "app.api.routes.passport_pipeline.SourceIngestionService.fetch_for_project",
            new_callable=AsyncMock, return_value=mock_fetch,
        ) as mock_fetch_call, patch(
            "app.api.routes.passport_pipeline.SourceParsingService.parse_source_document",
            new_callable=AsyncMock,
        ) as mock_parse, patch(
            "app.api.routes.passport_pipeline.PassportEngine.generate_draft",
            new_callable=AsyncMock,
        ) as mock_proj:
            async with client as c:
                resp = await c.post(
                    f"/v1/projects/{project_id}/passport-pipeline",
                    json={"ehr_code": "101035685"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 502
    body = resp.json()
    assert body["status"] == "fetch_failed"
    assert body["stage"] == "fetch"
    assert "error" in body
    assert body["source_document_id"] == str(source_doc_id)
    assert body["extraction_run_id"] is None
    mock_parse.assert_not_called()
    mock_proj.assert_not_called()


# ---------------------------------------------------------------------------
# Unit: short-circuit on parse failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_short_circuits_on_parse_failure() -> None:
    """Parse failure → stage='parse'; source_document_id set, extraction_run_id null."""
    import os

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/fake")
    os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

    from app.main import app

    project_id = uuid4()
    source_doc_id = uuid4()

    mock_fetch = FetchResult(
        status="ok", source_document_id=source_doc_id,
        source_type="ehr_pdf", fetch_status="ok",
    )
    mock_parse = ParseResult(
        status="parse_failed",
        error="storage_download_failed: bucket not found",
    )

    db = _mock_db()
    client = await _make_client(app, db)

    try:
        with patch(
            "app.api.routes.passport_pipeline.SourceIngestionService.fetch_for_project",
            new_callable=AsyncMock, return_value=mock_fetch,
        ), patch(
            "app.api.routes.passport_pipeline.SourceParsingService.parse_source_document",
            new_callable=AsyncMock, return_value=mock_parse,
        ), patch(
            "app.api.routes.passport_pipeline.PassportEngine.generate_draft",
            new_callable=AsyncMock,
        ) as mock_proj:
            async with client as c:
                resp = await c.post(
                    f"/v1/projects/{project_id}/passport-pipeline",
                    json={"ehr_code": "101035685"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 502
    body = resp.json()
    assert body["status"] == "parse_failed"
    assert body["stage"] == "parse"
    assert body["source_document_id"] == str(source_doc_id)
    assert body["extraction_run_id"] is None
    mock_proj.assert_not_called()


# ---------------------------------------------------------------------------
# Unit: deduped fetch skips re-parse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_skips_reparse_for_deduped_fetch() -> None:
    """Deduped fetch + existing completed run → parse_source_document not called."""
    import os

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/fake")
    os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

    from app.main import app

    project_id = uuid4()
    source_doc_id = uuid4()
    existing_run_id = uuid4()
    draft_id = uuid4()

    mock_fetch = FetchResult(
        status="ok", source_document_id=source_doc_id,
        source_type="ehr_pdf", fetch_status="deduped",
    )
    existing_run = MagicMock(spec=ExtractionRun)
    existing_run.id = existing_run_id
    existing_run.status = "completed"

    mock_proj = ProjectionResult(
        passport_draft_id=draft_id,
        schema_version="buildloop.passport.mvp.v1",
        schema_completeness_score=81.6,
        confidence_score=95.0,
        building_id=uuid4(),
        project_id=project_id,
        status="draft_system_generated",
        generated_at="2026-05-09T10:00:00+00:00",
        payload_json={
            "identity": {}, "building_profile": {}, "structural_systems": {},
            "technical_systems": {}, "location": {}, "building_parts": {},
            "quality": {"schema_completeness_score": 81.6, "confidence_score": 95.0,
                        "confidence_label": "high", "section_breakdown": {}, "missing_fields": []},
        },
    )

    db = _mock_db()
    client = await _make_client(app, db)

    try:
        with patch(
            "app.api.routes.passport_pipeline.SourceIngestionService.fetch_for_project",
            new_callable=AsyncMock, return_value=mock_fetch,
        ), patch(
            "app.api.routes.passport_pipeline._latest_completed_run",
            new_callable=AsyncMock, return_value=existing_run,
        ), patch(
            "app.api.routes.passport_pipeline._count_observations",
            new_callable=AsyncMock, return_value=31,
        ), patch(
            "app.api.routes.passport_pipeline.SourceParsingService.parse_source_document",
            new_callable=AsyncMock,
        ) as mock_parse, patch(
            "app.api.routes.passport_pipeline.PassportEngine.generate_draft",
            new_callable=AsyncMock, return_value=mock_proj,
        ):
            async with client as c:
                resp = await c.post(
                    f"/v1/projects/{project_id}/passport-pipeline",
                    json={"ehr_code": "101035685"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["fetch_status"] == "deduped"
    assert body["extraction_run_id"] == str(existing_run_id)
    assert body["observation_count"] == 31
    mock_parse.assert_not_called()


# ---------------------------------------------------------------------------
# Integration: real services, mocked EHR HTTP + storage I/O
# ---------------------------------------------------------------------------


class _PipelineMockDB:
    """Stateful mock DB for the integration test; tracks objects across three services."""

    def __init__(self, project_id: UUID, building_id: UUID) -> None:
        self._project = MagicMock(spec=Project)
        self._project.id = project_id
        self._project.building_id = building_id

        self._source_docs: dict[UUID, SourceDocument] = {}
        self._extraction_runs: dict[UUID, ExtractionRun] = {}
        self._observations: list[Observation] = []
        self._draft: PassportDraft | None = None
        self._execute_count = 0

    async def get(self, model_class: type, pk: UUID, *args: Any, **kwargs: Any) -> Any:
        if model_class is Project:
            return self._project
        if model_class is SourceDocument:
            return self._source_docs.get(pk)
        return None

    def add(self, obj: Any) -> None:
        if isinstance(obj, SourceDocument):
            self._source_docs[obj.id] = obj
        elif isinstance(obj, ExtractionRun):
            self._extraction_runs[obj.id] = obj
        elif isinstance(obj, Observation):
            self._observations.append(obj)
        elif isinstance(obj, PassportDraft):
            self._draft = obj
            if not obj.id:
                obj.id = uuid4()

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: Any) -> None:
        if isinstance(obj, PassportDraft) and not obj.id:
            obj.id = uuid4()

    async def execute(self, stmt: Any) -> Any:
        self._execute_count += 1
        n = self._execute_count
        mock_result = MagicMock()

        if n == 1:
            # SourceIngestionService: dedup check → no existing doc
            mock_result.scalar_one_or_none.return_value = None
        elif n == 2:
            # PassportEngine: latest completed ExtractionRun
            latest = (
                list(self._extraction_runs.values())[-1]
                if self._extraction_runs else None
            )
            mock_result.scalar_one_or_none.return_value = latest
        elif n == 3:
            # PassportEngine: observations for the run
            mock_result.scalars.return_value.all.return_value = list(self._observations)
        elif n == 4:
            # PassportEngine: existing PassportDraft → None (create new)
            mock_result.scalar_one_or_none.return_value = None
        else:
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []

        return mock_result

    def get_added_draft(self) -> PassportDraft | None:
        return self._draft


@pytest.mark.asyncio
async def test_pipeline_integration_against_lai_1() -> None:
    """End-to-end pipeline with real services; only EHR HTTP + storage are mocked.

    Confirms heated_area_m2.value=4971.8 in the resulting draft — the same
    value verified in the session 2.5 live smoke test.
    """
    assert _FIXTURE_PDF.exists(), f"Fixture PDF not found: {_FIXTURE_PDF}"
    pdf_bytes = _FIXTURE_PDF.read_bytes()
    checksum = hashlib.sha256(pdf_bytes).hexdigest()

    from app.services.source_ingestion.service import SourceIngestionService
    from app.services.source_ingestion.types import EhrFetchResult
    from app.services.source_parsing.service import SourceParsingService
    from app.services.passport_engine.service import PassportEngine

    project_id = uuid4()
    building_id = uuid4()
    db = _PipelineMockDB(project_id=project_id, building_id=building_id)

    fake_ehr_result = EhrFetchResult(
        ok=True,
        content=pdf_bytes,
        checksum=checksum,
        source_uri="https://ehr-test.example.com/101035685",
        error=None,
        ssl_fallback_used=False,
        status_code=200,
        fetch_metadata={"url": "...", "http_code": 200, "bytes": len(pdf_bytes)},
    )
    mock_fetcher = MagicMock()
    mock_fetcher.fetch_pdf = AsyncMock(return_value=fake_ehr_result)

    async def _fake_download(bucket: str, path: str) -> bytes:
        return pdf_bytes

    with patch(
        "app.services.source_ingestion.service.storage_module.upload_ehr_pdf",
        new_callable=AsyncMock,
        return_value=("test-bucket", "ehr/101035685.pdf"),
    ):
        # Stage 1: fetch
        svc = SourceIngestionService(fetcher=mock_fetcher)
        fetch_result = await svc.fetch_for_project(project_id, "101035685", db)  # type: ignore[arg-type]
        assert fetch_result.status == "ok", f"Fetch failed: {fetch_result.error}"
        source_doc_id: UUID = fetch_result.source_document_id  # type: ignore[assignment]

        # Stage 2: parse (pass fake storage download directly)
        parse_result = await SourceParsingService().parse_source_document(
            source_doc_id, db, storage_client=_fake_download  # type: ignore[arg-type]
        )
        assert parse_result.status == "ok", f"Parse failed: {parse_result.error}"
        assert parse_result.observation_count > 0

        # Stage 3: project
        engine = PassportEngine()
        projection = await engine.generate_draft(project_id, db)  # type: ignore[arg-type]

    assert projection.schema_completeness_score > 0.0

    draft = db.get_added_draft()
    assert draft is not None, "PassportDraft was not persisted"

    payload = draft.payload_json
    heated_area = payload["building_profile"]["heated_area_m2"]["value"]
    assert heated_area == 4971.8, f"Expected 4971.8, got {heated_area}"

    # Sanity-check the overall structure
    assert payload["identity"]["ehr_code"]["value"] == "101035685"
    assert len(payload["building_parts"]["parts"]) >= 1
    completeness = payload["quality"]["schema_completeness_score"]
    assert 78.0 <= completeness <= 85.0, f"Completeness {completeness} outside expected range"
