"""Integration tests for ResolverService.

Mocks both the InAdsAdapter and the SQLAlchemy AsyncSession so the suite
runs without a live database or network. The tests verify that the service:
  - returns the correct ResolutionStatus for each fixture scenario
  - preserves corner-address aliases in the resolved result
  - boosts confidence when the same EHR appears across multiple variants
  - writes expected DB objects (ResolverRun, ResolverCandidate, Building)
  - select_candidate promotes an ambiguous run to resolved
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.services.resolver.inads_adapter import InAdsAdapter
from app.services.resolver.service import ResolverService
from app.services.resolver.types import InAdsResponse, ResolutionStatus

FIXTURES = Path(__file__).parent / "fixtures" / "inads_responses"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _make_mock_db(
    address: str,
    project_id: UUID | None = None,
) -> Any:
    """Return a mock AsyncSession pre-loaded with an IntakeRequest and Project."""
    from app.models.intake_requests import IntakeRequest
    from app.models.projects import Project

    pid = project_id or uuid4()

    mock_intake = MagicMock(spec=IntakeRequest)
    mock_intake.id = uuid4()
    mock_intake.raw_address_input = address
    mock_intake.normalized_input = {"project_id": str(pid)}
    mock_intake.status = "received"

    mock_project = MagicMock(spec=Project)
    mock_project.id = pid
    mock_project.raw_input_address = address
    mock_project.building_id = None

    mock_db = AsyncMock()

    async def _get(model_class: Any, pk: Any, *args: Any, **kwargs: Any) -> Any:
        from app.models.intake_requests import IntakeRequest as IR
        from app.models.projects import Project as Proj
        if model_class is IR:
            return mock_intake
        if model_class is Proj:
            return mock_project
        return None

    mock_db.get.side_effect = _get
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()

    # Default: no existing building found
    mock_no_building = MagicMock()
    mock_no_building.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_no_building

    return mock_db


def _make_adapter(fixture_name: str) -> InAdsAdapter:
    """Return a mock InAdsAdapter that always returns the given fixture."""
    data = _load_fixture(fixture_name)
    adapter = MagicMock(spec=InAdsAdapter)
    adapter.search = AsyncMock(return_value=InAdsResponse(ok=True, data=data))
    return adapter


# ---------------------------------------------------------------------------
# resolve() tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_clean_single_match_returns_resolved() -> None:
    """lai_1_resolved.json → status=resolved with ehr_code=101035685."""
    adapter = _make_adapter("lai_1_resolved.json")
    svc = ResolverService(adapter=adapter)
    mock_db = _make_mock_db("Lai 1, Tallinn")

    result = await svc.resolve(uuid4(), mock_db)

    assert result.status == ResolutionStatus.RESOLVED
    assert result.ehr_code == "101035685"
    assert result.confidence_score is not None
    assert result.confidence_score >= 0.85


@pytest.mark.asyncio
async def test_resolve_corner_address_preserves_aliases() -> None:
    """lai_1_corner.json → resolved, normalized_address contains '//', aliases extracted.

    Acceptance criterion (doc 12 Agent 2):
      'Lai 1, 10133 Tallinn' must return normalized_address containing '//'
      and address_aliases listing both street names.
    """
    adapter = _make_adapter("lai_1_corner.json")
    svc = ResolverService(adapter=adapter)
    mock_db = _make_mock_db("Lai 1, Tallinn")

    result = await svc.resolve(uuid4(), mock_db)

    assert result.status == ResolutionStatus.RESOLVED
    assert result.ehr_code == "101035685"
    assert result.normalized_address is not None
    assert "//" in result.normalized_address, (
        f"Expected '//' in normalized_address, got: {result.normalized_address!r}"
    )
    assert "Lai tn 1" in result.address_aliases, f"address_aliases={result.address_aliases}"
    assert "Nunne tn 4" in result.address_aliases, f"address_aliases={result.address_aliases}"


@pytest.mark.asyncio
async def test_resolve_ambiguous_returns_candidates() -> None:
    """pelguranna_ambiguous.json → status=ambiguous with multiple candidates."""
    adapter = _make_adapter("pelguranna_ambiguous.json")
    svc = ResolverService(adapter=adapter)
    mock_db = _make_mock_db("Pelguranna, Tallinn")

    result = await svc.resolve(uuid4(), mock_db)

    assert result.status == ResolutionStatus.AMBIGUOUS
    assert len(result.candidates) >= 2
    # All candidates must be in [0.50, 0.85)
    for c in result.candidates:
        assert c.confidence_score < 0.85
        assert c.confidence_score >= 0.50


@pytest.mark.asyncio
async def test_resolve_gibberish_returns_unresolved() -> None:
    """gibberish_unresolved.json → status=unresolved, no candidates."""
    adapter = _make_adapter("gibberish_unresolved.json")
    svc = ResolverService(adapter=adapter)
    mock_db = _make_mock_db("xyzxyz bloop 999, nowhere")

    result = await svc.resolve(uuid4(), mock_db)

    assert result.status == ResolutionStatus.UNRESOLVED
    assert result.reason == "no_extractable_ehr_code_found"


@pytest.mark.asyncio
async def test_resolve_multi_variant_boosts_confidence() -> None:
    """Same EHR code across multiple variants → confidence boosted.

    Acceptance criterion (doc 12 Agent 2).
    We force the adapter to return the same fixture for all variants and
    verify that the matched_variants list on the scored candidate has > 1 entry,
    triggering the multi-variant bonus in score_candidate().
    """
    data = _load_fixture("lai_1_resolved.json")
    adapter = MagicMock(spec=InAdsAdapter)
    adapter.search = AsyncMock(return_value=InAdsResponse(ok=True, data=data))

    svc = ResolverService(adapter=adapter)
    mock_db = _make_mock_db("Lai tn 1, Tallinn")  # has tn → alternate variant differs

    result = await svc.resolve(uuid4(), mock_db)

    assert result.status == ResolutionStatus.RESOLVED
    # adapter.search should have been called at least twice (exact + alternate)
    assert adapter.search.call_count >= 2

    # The winning candidate should reflect multi-variant matching
    if result.candidates:
        top = result.candidates[0]
        assert any("multi_variant_match" in r for r in top.match_reasons), (
            f"Expected multi_variant_match bonus; reasons={top.match_reasons}"
        )


@pytest.mark.asyncio
async def test_resolve_persists_resolver_run() -> None:
    """ResolverService.resolve() must call db.add() with a ResolverRun."""
    from app.models.resolver_runs import ResolverRun

    adapter = _make_adapter("lai_1_resolved.json")
    svc = ResolverService(adapter=adapter)
    mock_db = _make_mock_db("Lai 1, Tallinn")

    await svc.resolve(uuid4(), mock_db)

    added_types = [type(c.args[0]).__name__ for c in mock_db.add.call_args_list]
    assert "ResolverRun" in added_types


@pytest.mark.asyncio
async def test_resolve_persists_candidates() -> None:
    """ResolverService.resolve() must add at least one ResolverCandidate."""
    adapter = _make_adapter("lai_1_resolved.json")
    svc = ResolverService(adapter=adapter)
    mock_db = _make_mock_db("Lai 1, Tallinn")

    await svc.resolve(uuid4(), mock_db)

    added_types = [type(c.args[0]).__name__ for c in mock_db.add.call_args_list]
    assert "ResolverCandidate" in added_types


@pytest.mark.asyncio
async def test_resolve_not_found_raises() -> None:
    """resolve() with unknown intake_request_id raises ValueError."""
    adapter = _make_adapter("lai_1_resolved.json")
    svc = ResolverService(adapter=adapter)

    mock_db = AsyncMock()
    mock_db.get.return_value = None  # not found

    with pytest.raises(ValueError, match="not found"):
        await svc.resolve(uuid4(), mock_db)


# ---------------------------------------------------------------------------
# select_candidate() tests
# ---------------------------------------------------------------------------


def _make_select_db(ehr_code: str, run_id: UUID) -> Any:
    """Mock DB for select_candidate — returns an ambiguous run + two candidates."""
    from app.models.projects import Project
    from app.models.resolver_runs import ResolverCandidate, ResolverRun

    mock_run = MagicMock(spec=ResolverRun)
    mock_run.id = run_id
    mock_run.status = "ambiguous"
    mock_run.project_id = uuid4()

    mock_cand1 = MagicMock(spec=ResolverCandidate)
    mock_cand1.ehr_code = ehr_code
    mock_cand1.normalized_address = "Tallinn, Test tn 1"
    mock_cand1.address_aliases = []
    mock_cand1.confidence_score = 0.60
    mock_cand1.primary_candidate = False

    mock_cand2 = MagicMock(spec=ResolverCandidate)
    mock_cand2.ehr_code = "999999999"
    mock_cand2.normalized_address = "Tallinn, Other tn 2"
    mock_cand2.address_aliases = []
    mock_cand2.confidence_score = 0.55
    mock_cand2.primary_candidate = False

    mock_project = MagicMock(spec=Project)
    mock_project.id = mock_run.project_id
    mock_project.building_id = None

    mock_db = AsyncMock()

    async def _get(model_class: Any, pk: Any, *args: Any, **kwargs: Any) -> Any:
        from app.models.projects import Project as Proj
        from app.models.resolver_runs import ResolverRun as RR
        if model_class is RR:
            return mock_run
        if model_class is Proj:
            return mock_project
        return None

    mock_db.get.side_effect = _get
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()

    # execute() calls: 1) candidates query, 2) building lookup
    mock_cands_result = MagicMock()
    mock_cands_result.scalars.return_value.all.return_value = [mock_cand1, mock_cand2]

    mock_building_result = MagicMock()
    mock_building_result.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [mock_cands_result, mock_building_result]

    return mock_db


@pytest.mark.asyncio
async def test_select_candidate_returns_resolved() -> None:
    run_id = uuid4()
    chosen_ehr = "123456789"
    mock_db = _make_select_db(chosen_ehr, run_id)

    svc = ResolverService()
    result = await svc.select_candidate(run_id, chosen_ehr, mock_db)

    assert result.status == ResolutionStatus.RESOLVED
    assert result.ehr_code == chosen_ehr
    assert result.resolution_run_id == run_id


@pytest.mark.asyncio
async def test_select_candidate_unknown_ehr_raises() -> None:
    run_id = uuid4()
    mock_db = _make_select_db("123456789", run_id)

    svc = ResolverService()
    with pytest.raises(ValueError, match="not among candidates"):
        await svc.select_candidate(run_id, "000000000", mock_db)


@pytest.mark.asyncio
async def test_select_candidate_unknown_run_raises() -> None:
    mock_db = AsyncMock()
    mock_db.get.return_value = None

    svc = ResolverService()
    with pytest.raises(ValueError, match="not found"):
        await svc.select_candidate(uuid4(), "123456789", mock_db)
