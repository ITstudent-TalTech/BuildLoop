"""Tests for quality scoring functions.

All tests are pure-function; no DB access.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.services.passport_engine.projection import (
    CANONICAL_FIELDS,
    project_observations_to_passport,
)
from app.services.passport_engine.quality import (
    compute_confidence_score,
    compute_schema_completeness,
    derive_section_breakdown,
    list_missing_fields,
)
from app.services.passport_engine.tests.conftest import (
    GOLDEN_FILE_PATH,
    make_obs,
    make_source_doc,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings(high=0.95, medium=0.70, low=0.40, default=0.50) -> Settings:
    s = MagicMock(spec=Settings)
    s.passport_confidence_weight_high = high
    s.passport_confidence_weight_medium = medium
    s.passport_confidence_weight_low = low
    s.passport_confidence_weight_default = default
    return s


def _full_payload():
    """Build a fully populated payload from synthetic observations."""
    from app.services.relevance_engine.policy import classify

    obs_list = []
    for section, fields in CANONICAL_FIELDS.items():
        for field in fields:
            if section == "building_parts" and field == "parts":
                # Actual obs key is "building_parts", not "parts"
                obs = make_obs("building_parts", "building_parts", [
                    {"part_identifier": "part_1", "part_type": "T",
                     "part_name": "N", "part_use": "U", "part_area_m2": 100.0}
                ])
                obs.relevance_class = "passport_core"
                obs_list.append(obs)
            elif field == "floors":
                # Aggregated from two sub-observations
                obs = make_obs("building_profile", "floors.above_ground", 4)
                obs.relevance_class = "passport_core"
                obs_list.append(obs)
            else:
                obs = make_obs(section, field, "synthetic_value")
                obs.relevance_class = classify(section, field)
                obs_list.append(obs)

    return project_observations_to_passport(obs_list, make_source_doc())


def _empty_payload():
    return project_observations_to_passport([], make_source_doc())


# ---------------------------------------------------------------------------
# compute_schema_completeness
# ---------------------------------------------------------------------------

def test_completeness_full_passport_is_100() -> None:
    payload = _full_payload()
    score = compute_schema_completeness(payload)
    assert score == 100.0


def test_completeness_empty_passport_is_0() -> None:
    payload = _empty_payload()
    score = compute_schema_completeness(payload)
    assert score == 0.0


def test_completeness_partial_calculation() -> None:
    """Only identity.ehr_code populated → 1/38 ≈ 2.6%."""
    obs = make_obs("identity", "ehr_code", "101035685")
    obs.relevance_class = "passport_core"
    payload = project_observations_to_passport([obs], make_source_doc())
    score = compute_schema_completeness(payload)

    total_fields = sum(len(v) for v in CANONICAL_FIELDS.values())
    expected = round(1 / total_fields * 100, 1)
    assert score == expected


# ---------------------------------------------------------------------------
# compute_confidence_score
# ---------------------------------------------------------------------------

def test_confidence_score_weighted_correctly() -> None:
    """All-high observations → score near 95.0."""
    settings = _make_settings()
    observations = [
        make_obs("identity", "ehr_code", "X"),
        make_obs("identity", "country", "EE"),
    ]
    for obs in observations:
        obs.relevance_class = "passport_core"
    score = compute_confidence_score(observations, settings)
    assert score == pytest.approx(95.0, abs=0.1)


def test_confidence_score_mixed_labels() -> None:
    """Mix of high and low → weighted average."""
    settings = _make_settings(high=0.95, low=0.40)
    high_obs = make_obs("identity", "ehr_code", "X", confidence_label="high")
    low_obs = make_obs("identity", "country", "EE", confidence_label="low")
    high_obs.relevance_class = "passport_core"
    low_obs.relevance_class = "passport_core"

    score = compute_confidence_score([high_obs, low_obs], settings)
    expected = round((0.95 + 0.40) / 2 * 100, 1)
    assert score == pytest.approx(expected, abs=0.1)


def test_confidence_score_empty_observations_is_zero() -> None:
    settings = _make_settings()
    assert compute_confidence_score([], settings) == 0.0


# ---------------------------------------------------------------------------
# derive_section_breakdown
# ---------------------------------------------------------------------------

def test_section_breakdown_per_section() -> None:
    """section_breakdown contains every canonical section."""
    payload = _empty_payload()
    breakdown = derive_section_breakdown(payload)

    for section in CANONICAL_FIELDS:
        assert section in breakdown
        entry = breakdown[section]
        assert "fields_populated" in entry
        assert "fields_total" in entry
        assert "confidence_label" in entry
        assert entry["fields_total"] == len(CANONICAL_FIELDS[section])
        assert entry["fields_populated"] == 0


def test_section_breakdown_populated_counts() -> None:
    """Populated fields increment fields_populated correctly."""
    obs1 = make_obs("identity", "ehr_code", "101035685")
    obs1.relevance_class = "passport_core"
    obs2 = make_obs("identity", "country", "EE")
    obs2.relevance_class = "passport_core"
    payload = project_observations_to_passport([obs1, obs2], make_source_doc())

    breakdown = derive_section_breakdown(payload)
    assert breakdown["identity"]["fields_populated"] == 2
    assert breakdown["identity"]["fields_total"] == len(CANONICAL_FIELDS["identity"])


# ---------------------------------------------------------------------------
# list_missing_fields
# ---------------------------------------------------------------------------

def test_missing_fields_list_correct() -> None:
    """Empty payload → all canonical fields listed as missing."""
    payload = _empty_payload()
    missing = list_missing_fields(payload)

    total_expected = sum(len(v) for v in CANONICAL_FIELDS.values())
    assert len(missing) == total_expected
    assert "identity.ehr_code" in missing
    assert "building_profile.heated_area_m2" in missing
    assert "structural_systems.foundation_type" in missing
    assert "building_parts.parts" in missing


def test_missing_fields_excludes_populated_fields() -> None:
    """Populated fields must NOT appear in missing_fields."""
    obs = make_obs("identity", "ehr_code", "101035685")
    obs.relevance_class = "passport_core"
    payload = project_observations_to_passport([obs], make_source_doc())

    missing = list_missing_fields(payload)
    assert "identity.ehr_code" not in missing


# ---------------------------------------------------------------------------
# Lai 1 golden data integration check
# ---------------------------------------------------------------------------

def test_lai_1_completeness_score() -> None:
    """Lai 1 observations (31) produce completeness ≈ 81.6% (31/38 × 100)."""
    assert GOLDEN_FILE_PATH.exists(), "Run source_parsing tests first to generate golden file."
    golden = json.loads(GOLDEN_FILE_PATH.read_text(encoding="utf-8"))

    from app.services.relevance_engine.policy import classify

    observations = []
    for entry in golden:
        obs = make_obs(
            entry["namespace"], entry["key"], entry["value"],
            unit=entry.get("unit"),
            confidence_label=entry.get("confidence_label") or "high",
            page_number=entry.get("page_number"),
        )
        obs.relevance_class = classify(obs.namespace, obs.key)
        observations.append(obs)

    payload = project_observations_to_passport(observations, make_source_doc())
    score = compute_schema_completeness(payload)

    # 31 out of 38 canonical fields populated (verified manually)
    # Expected: 31/38 * 100 = 81.6%
    assert 78.0 <= score <= 85.0, f"Completeness {score} outside expected 78-85% range"
