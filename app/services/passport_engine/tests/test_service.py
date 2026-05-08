"""Integration-style tests for PassportEngine service.

All DB interactions are mocked — no live Supabase needed.
The Lai 1 golden file (31 observations) is used for the core acceptance test.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.models.extraction_runs import ExtractionRun
from app.models.observations import Observation
from app.models.passport_drafts import PassportDraft
from app.models.projects import Project
from app.models.source_documents import SourceDocument
from app.services.passport_engine.service import PassportEngine
from app.services.passport_engine.tests.conftest import (
    GOLDEN_FILE_PATH,
    _FIXED_DOC_ID,
    _FIXED_NOW,
    make_obs,
    make_source_doc,
)

_PROJECT_ID = UUID("f328b30a-3504-4ced-a675-629922b06dc2")
_RUN_ID = uuid4()
_DOC_ID = _FIXED_DOC_ID


# ---------------------------------------------------------------------------
# Mock DB helpers
# ---------------------------------------------------------------------------

def _make_project(project_id: UUID = _PROJECT_ID) -> MagicMock:
    p = MagicMock(spec=Project)
    p.id = project_id
    p.building_id = uuid4()
    return p


def _make_extraction_run(run_id: UUID = _RUN_ID, source_doc_id: UUID = _DOC_ID) -> MagicMock:
    run = MagicMock(spec=ExtractionRun)
    run.id = run_id
    run.source_document_id = source_doc_id
    run.status = "completed"
    run.completed_at = _FIXED_NOW
    return run


def _make_db(
    *,
    project: Any,
    extraction_run: Any,
    observations: list[Observation],
    source_doc: Any,
    existing_draft: Any = None,
) -> AsyncMock:
    db = AsyncMock()

    async def _get(model_class, pk, *args, **kwargs):
        if model_class is Project:
            return project
        if model_class is SourceDocument:
            return source_doc
        if model_class is PassportDraft:
            return None
        return None

    db.get.side_effect = _get

    call_count = [0]

    async def _execute(stmt, *args, **kwargs):
        call_count[0] += 1
        mock_result = MagicMock()
        n = call_count[0]
        if n == 1:
            # ExtractionRun query
            mock_result.scalar_one_or_none.return_value = extraction_run
        elif n == 2:
            # Observations query
            mock_result.scalars.return_value.all.return_value = observations
        elif n == 3:
            # PassportDraft upsert query
            mock_result.scalar_one_or_none.return_value = existing_draft
        else:
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
        return mock_result

    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    return db


def _load_lai_1_observations() -> list[Observation]:
    """Load 31 Lai 1 observations from the golden file."""
    assert GOLDEN_FILE_PATH.exists(), (
        f"Golden file not found: {GOLDEN_FILE_PATH}. "
        "Run source_parsing tests first."
    )
    from app.services.relevance_engine.policy import classify

    golden = json.loads(GOLDEN_FILE_PATH.read_text(encoding="utf-8"))
    observations = []
    for entry in golden:
        obs = make_obs(
            entry["namespace"],
            entry["key"],
            entry["value"],
            unit=entry.get("unit"),
            confidence_label=entry.get("confidence_label") or "high",
            page_number=entry.get("page_number"),
        )
        obs.relevance_class = classify(obs.namespace, obs.key)
        observations.append(obs)
    return observations


# ---------------------------------------------------------------------------
# Acceptance tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_draft_against_lai_1_observations() -> None:
    """Projecting 31 Lai 1 observations produces expected passport values."""
    observations = _load_lai_1_observations()
    project = _make_project()
    run = _make_extraction_run()
    doc = make_source_doc(_DOC_ID)
    db = _make_db(
        project=project,
        extraction_run=run,
        observations=observations,
        source_doc=doc,
    )
    # Capture the passport_draft added to session
    added_drafts: list[PassportDraft] = []

    def _capture_add(obj):
        if isinstance(obj, PassportDraft):
            added_drafts.append(obj)

    db.add = MagicMock(side_effect=_capture_add)

    async def _fake_refresh(obj):
        if isinstance(obj, PassportDraft) and not hasattr(obj, "id"):
            obj.id = uuid4()
        if not hasattr(obj, "schema_completeness_score") or obj.schema_completeness_score is None:
            pass  # object already populated inline

    db.refresh = AsyncMock(side_effect=_fake_refresh)

    engine = PassportEngine()
    result = await engine.generate_draft(_PROJECT_ID, db)

    assert result.schema_version == "buildloop.passport.mvp.v1"
    assert result.schema_completeness_score > 0.0
    assert result.confidence_score > 0.0

    # Inspect the draft that was passed to db.add
    assert len(added_drafts) == 1
    draft_payload = added_drafts[0].payload_json

    assert draft_payload["identity"]["ehr_code"]["value"] == "101035685"
    assert draft_payload["building_profile"]["heated_area_m2"]["value"] == 4971.8
    assert len(draft_payload["building_parts"]["parts"]) == 3
    assert draft_payload["structural_systems"]["load_bearing_material"]["value"] is not None
    assert draft_payload["technical_systems"]["electricity"]["value"] == "võrk"

    # Completeness: 31/38 ≈ 81.6%
    score = draft_payload["quality"]["schema_completeness_score"]
    assert 78.0 <= score <= 85.0, f"Completeness {score} outside expected range"


@pytest.mark.asyncio
async def test_generate_draft_handles_empty_observations() -> None:
    """Empty extraction run → all-null passport, 0% completeness."""
    project = _make_project()
    run = _make_extraction_run()
    doc = make_source_doc(_DOC_ID)
    db = _make_db(project=project, extraction_run=run, observations=[], source_doc=doc)

    added_drafts: list[PassportDraft] = []
    db.add = MagicMock(side_effect=lambda o: added_drafts.append(o) if isinstance(o, PassportDraft) else None)
    db.refresh = AsyncMock()

    engine = PassportEngine()
    result = await engine.generate_draft(_PROJECT_ID, db)

    assert len(added_drafts) == 1
    payload = added_drafts[0].payload_json
    assert payload["quality"]["schema_completeness_score"] == 0.0
    assert payload["identity"]["ehr_code"]["value"] is None


@pytest.mark.asyncio
async def test_generate_draft_is_idempotent() -> None:
    """Re-running generate_draft updates the existing draft (not creates new one)."""
    observations = _load_lai_1_observations()
    project = _make_project()
    run = _make_extraction_run()
    doc = make_source_doc(_DOC_ID)

    # Simulate existing draft
    existing = MagicMock(spec=PassportDraft)
    existing.id = uuid4()
    existing.payload_json = {}
    existing.schema_completeness_score = 0.0
    existing.confidence_score = 0.0
    existing.generated_at = _FIXED_NOW

    db = _make_db(
        project=project,
        extraction_run=run,
        observations=observations,
        source_doc=doc,
        existing_draft=existing,
    )
    db.refresh = AsyncMock()

    engine = PassportEngine()
    result = await engine.generate_draft(_PROJECT_ID, db)

    # Should UPDATE (not add) the existing draft
    db.add.assert_not_called()
    assert existing.payload_json != {}  # was updated in-place
    assert existing.schema_completeness_score > 0.0


@pytest.mark.asyncio
async def test_generate_draft_raises_when_project_not_found() -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    engine = PassportEngine()
    with pytest.raises(ValueError, match="not found"):
        await engine.generate_draft(uuid4(), db)


@pytest.mark.asyncio
async def test_generate_draft_raises_when_no_extraction_run() -> None:
    project = _make_project()
    db = AsyncMock()

    async def _get(model_class, pk, *args, **kwargs):
        if model_class is Project:
            return project
        return None

    db.get.side_effect = _get
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    engine = PassportEngine()
    with pytest.raises(ValueError, match="No completed extraction run"):
        await engine.generate_draft(_PROJECT_ID, db)


@pytest.mark.asyncio
async def test_get_current_draft_returns_none_when_no_draft() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    engine = PassportEngine()
    draft = await engine.get_current_draft(_PROJECT_ID, db)
    assert draft is None
