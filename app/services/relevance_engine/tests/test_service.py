"""Tests for RelevanceEngine service.

All tests mock AsyncSession — no live DB required.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call
from uuid import UUID, uuid4

import pytest

from app.models.observations import Observation
from app.services.relevance_engine.service import RelevanceEngine
from app.services.relevance_engine.types import ClassificationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_obs(namespace: str, key: str, relevance_class: str = "unclassified") -> Observation:
    obs = MagicMock(spec=Observation)
    obs.id = uuid4()
    obs.namespace = namespace
    obs.key = key
    obs.relevance_class = relevance_class
    obs.created_at = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)
    return obs


def _make_db(observations: list[Observation]) -> AsyncMock:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = observations
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# classify_observation — pure function tests
# ---------------------------------------------------------------------------

def test_classify_observation_passport_core() -> None:
    engine = RelevanceEngine()
    obs = _make_obs("identity", "ehr_code")
    assert engine.classify_observation(obs) == "passport_core"


def test_classify_observation_passport_supporting() -> None:
    engine = RelevanceEngine()
    obs = _make_obs("building_profile", "building_name")
    assert engine.classify_observation(obs) == "passport_supporting"


def test_classify_observation_low_signal_for_unknown() -> None:
    engine = RelevanceEngine()
    obs = _make_obs("unknown_namespace", "some_key")
    assert engine.classify_observation(obs) == "low_signal"


# ---------------------------------------------------------------------------
# classify_extraction_run
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_classify_extraction_run_updates_observations() -> None:
    """All observations get their relevance_class updated to the policy bucket."""
    run_id = uuid4()
    observations = [
        _make_obs("identity", "ehr_code"),
        _make_obs("building_profile", "heated_area_m2"),
        _make_obs("building_profile", "building_name"),
        _make_obs("unknown_ns", "unknown_key"),
    ]
    db = _make_db(observations)
    engine = RelevanceEngine()
    result = await engine.classify_extraction_run(run_id, db)

    assert observations[0].relevance_class == "passport_core"
    assert observations[1].relevance_class == "passport_core"
    assert observations[2].relevance_class == "passport_supporting"
    assert observations[3].relevance_class == "low_signal"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_classify_is_idempotent() -> None:
    """Running classify twice on the same observations yields identical results."""
    run_id = uuid4()
    obs1 = _make_obs("identity", "ehr_code", relevance_class="unclassified")
    obs2 = _make_obs("building_profile", "building_name", relevance_class="unclassified")
    observations = [obs1, obs2]

    db = _make_db(observations)
    engine = RelevanceEngine()

    result1 = await engine.classify_extraction_run(run_id, db)
    # Reset mock result for second call (same observations, already classified)
    mock_result2 = MagicMock()
    mock_result2.scalars.return_value.all.return_value = observations
    db.execute = AsyncMock(return_value=mock_result2)

    result2 = await engine.classify_extraction_run(run_id, db)

    assert result1.bucket_counts == result2.bucket_counts
    assert obs1.relevance_class == "passport_core"
    assert obs2.relevance_class == "passport_supporting"


@pytest.mark.asyncio
async def test_bucket_counts_returned() -> None:
    """ClassificationResult.bucket_counts correctly tallies each bucket."""
    run_id = uuid4()
    observations = [
        _make_obs("identity", "ehr_code"),            # passport_core
        _make_obs("identity", "normalized_address"),  # passport_core
        _make_obs("building_profile", "building_name"),  # passport_supporting
        _make_obs("unknown_ns", "raw_thing"),          # low_signal
    ]
    db = _make_db(observations)
    engine = RelevanceEngine()
    result: ClassificationResult = await engine.classify_extraction_run(run_id, db)

    assert result.observations_classified == 4
    assert result.bucket_counts.get("passport_core", 0) == 2
    assert result.bucket_counts.get("passport_supporting", 0) == 1
    assert result.bucket_counts.get("low_signal", 0) == 1


@pytest.mark.asyncio
async def test_classify_extraction_run_empty_returns_zero() -> None:
    """Extraction run with no observations returns observations_classified=0."""
    run_id = uuid4()
    db = _make_db([])
    engine = RelevanceEngine()
    result = await engine.classify_extraction_run(run_id, db)

    assert result.observations_classified == 0
    assert result.bucket_counts == {}
    db.commit.assert_awaited_once()
