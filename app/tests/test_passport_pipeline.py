"""Tests for POST /v1/projects/{id}/passport-pipeline and -auto.

All service calls are mocked — no live DB or Supabase needed.
Focuses on the `draft` field being populated in the success response.
"""

from __future__ import annotations

import os
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

if TYPE_CHECKING:
    from app.services.passport_engine.types import ProjectionResult
    from app.services.source_ingestion.types import FetchResult
    from app.services.source_parsing.types import ParseResult

# Ensure env vars are set before importing the app
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/fake")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

_PROJECT_ID = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
_SOURCE_DOC_ID = uuid4()
_RUN_ID = uuid4()
_DRAFT_ID = uuid4()
_BUILDING_ID = uuid4()
_EHR_CODE = "101035685"


def _make_fetch_result(status: str = "ok", fetch_status: str = "ok") -> "FetchResult":
    from app.services.source_ingestion.types import FetchResult

    return FetchResult(
        status=status,
        source_document_id=_SOURCE_DOC_ID if status != "fetch_failed" else None,
        source_type="ehr_pdf",
        fetch_status=fetch_status,
        error=None if status == "ok" else "EHR fetch failed",
    )


def _make_parse_result(status: str = "ok") -> "ParseResult":
    from app.services.source_parsing.types import ParseResult

    return ParseResult(
        status=status,
        extraction_run_id=_RUN_ID if status == "ok" else None,
        observation_count=31 if status == "ok" else 0,
        error=None if status == "ok" else "parse error",
    )


def _make_projection_result() -> "ProjectionResult":
    from app.services.passport_engine.types import ProjectionResult

    return ProjectionResult(
        passport_draft_id=_DRAFT_ID,
        schema_version="buildloop.passport.mvp.v1",
        schema_completeness_score=81.6,
        confidence_score=95.0,
        building_id=_BUILDING_ID,
        project_id=_PROJECT_ID,
        status="draft_system_generated",
        generated_at="2026-05-09T10:00:00+00:00",
        payload_json={
            "identity": {"ehr_code": {"value": _EHR_CODE, "confidence": "high", "source": None, "last_updated": None}},
            "building_profile": {},
            "structural_systems": {},
            "technical_systems": {},
            "location": {},
            "building_parts": {},
            "quality": {
                "schema_completeness_score": 81.6,
                "confidence_score": 95.0,
                "confidence_label": "high",
                "section_breakdown": {},
                "missing_fields": [],
            },
        },
    )


def _mock_db_session_for_pipeline() -> AsyncMock:
    """Return an AsyncMock session that returns project+building for -auto lookups."""
    from app.models.buildings import Building
    from app.models.projects import Project

    project = MagicMock(spec=Project)
    project.id = _PROJECT_ID
    project.building_id = _BUILDING_ID

    building = MagicMock(spec=Building)
    building.id = _BUILDING_ID
    building.primary_ehr_code = _EHR_CODE

    db = AsyncMock()

    async def _get(model_class: type, pk: UUID, *args: object, **kwargs: object) -> object:
        if model_class is Project:
            return project
        if model_class is Building:
            return building
        return None

    db.get.side_effect = _get
    return db


# ── Helper context manager that patches all three pipeline services ────────────


def _patch_pipeline(
    fetch_result: FetchResult | None = None,
    parse_result: ParseResult | None = None,
    projection_result: ProjectionResult | None = None,
) -> tuple[AbstractContextManager[object], ...]:
    if fetch_result is None:
        fetch_result = _make_fetch_result()
    if parse_result is None:
        parse_result = _make_parse_result()
    if projection_result is None:
        projection_result = _make_projection_result()

    return (
        patch(
            "app.api.routes.passport_pipeline.SourceIngestionService.fetch_for_project",
            new_callable=AsyncMock,
            return_value=fetch_result,
        ),
        patch(
            "app.api.routes.passport_pipeline.SourceParsingService.parse_source_document",
            new_callable=AsyncMock,
            return_value=parse_result,
        ),
        patch(
            "app.api.routes.passport_pipeline.PassportEngine.generate_draft",
            new_callable=AsyncMock,
            return_value=projection_result,
        ),
        patch(
            "app.api.routes.passport_pipeline.get_session",
            return_value=_mock_db_session_for_pipeline(),
        ),
    )


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_success_includes_draft_field(test_client: AsyncClient) -> None:
    """POST /passport-pipeline → 200 with draft.identity.ehr_code populated."""
    from contextlib import AsyncExitStack

    patches = _patch_pipeline()
    async with AsyncExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        response = await test_client.post(
            f"/v1/projects/{_PROJECT_ID}/passport-pipeline",
            json={"ehr_code": _EHR_CODE},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["passport_draft_id"] == str(_DRAFT_ID)
    assert body["observation_count"] == 31
    assert body["fetch_status"] == "ok"

    # The key assertion: draft is populated inline, no second GET needed
    draft = body.get("draft")
    assert draft is not None, "draft must be present in pipeline success response"
    assert draft["identity"]["ehr_code"]["value"] == _EHR_CODE


@pytest.mark.asyncio
async def test_pipeline_auto_success_includes_draft_field() -> None:
    """POST /passport-pipeline-auto → 200 with draft populated.

    The -auto handler calls db.get(Project, ...) and db.get(Building, ...)
    before entering the shared pipeline, so we override get_session to return
    a mock that returns the right ORM objects.
    """
    from contextlib import AsyncExitStack

    from httpx import ASGITransport, AsyncClient as _AsyncClient

    from app.db.session import get_session
    from app.main import app as fastapi_app

    mock_db = _mock_db_session_for_pipeline()

    from collections.abc import AsyncGenerator
    from sqlalchemy.ext.asyncio import AsyncSession

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield mock_db

    fastapi_app.dependency_overrides[get_session] = _override_session
    try:
        patches = _patch_pipeline()
        async with AsyncExitStack() as stack:
            for p in patches:
                stack.enter_context(p)

            async with _AsyncClient(
                transport=ASGITransport(app=fastapi_app), base_url="http://testserver"
            ) as client:
                response = await client.post(
                    f"/v1/projects/{_PROJECT_ID}/passport-pipeline-auto"
                )
    finally:
        fastapi_app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    draft = body.get("draft")
    assert draft is not None
    assert draft["identity"]["ehr_code"]["value"] == _EHR_CODE


@pytest.mark.asyncio
async def test_pipeline_fetch_failure_returns_502(test_client: AsyncClient) -> None:
    """Fetch stage failure → 502 with status=fetch_failed, no draft."""
    from contextlib import AsyncExitStack

    patches = _patch_pipeline(fetch_result=_make_fetch_result(status="fetch_failed"))
    async with AsyncExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        response = await test_client.post(
            f"/v1/projects/{_PROJECT_ID}/passport-pipeline",
            json={"ehr_code": _EHR_CODE},
        )

    assert response.status_code == 502
    body = response.json()
    assert body["status"] == "fetch_failed"
    assert body["stage"] == "fetch"
    assert "draft" not in body


@pytest.mark.asyncio
async def test_pipeline_parse_failure_returns_502(test_client: AsyncClient) -> None:
    """Parse stage failure → 502 with status=parse_failed, no draft."""
    from contextlib import AsyncExitStack

    patches = _patch_pipeline(parse_result=_make_parse_result(status="parse_failed"))
    async with AsyncExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        response = await test_client.post(
            f"/v1/projects/{_PROJECT_ID}/passport-pipeline",
            json={"ehr_code": _EHR_CODE},
        )

    assert response.status_code == 502
    body = response.json()
    assert body["status"] == "parse_failed"
    assert body["stage"] == "parse"
