"""Pure-function tests for project_observations_to_passport().

No DB access — all observations are constructed with the make_obs helper.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.passport_engine.projection import project_observations_to_passport
from app.services.passport_engine.tests.conftest import (
    GOLDEN_FILE_PATH,
    _FIXED_DOC_ID,
    _FIXED_NOW,
    make_obs,
    make_source_doc,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify(obs_list):
    """Set relevance_class for a list of observations using the policy."""
    from app.services.relevance_engine.policy import classify
    for obs in obs_list:
        obs.relevance_class = classify(obs.namespace, obs.key)
    return obs_list


# ---------------------------------------------------------------------------
# Core contract tests
# ---------------------------------------------------------------------------

def test_projects_passport_core_only_no_low_signal() -> None:
    """low_signal observations must not appear in the projected passport."""
    observations = _classify([
        make_obs("identity", "ehr_code", "101035685"),
        make_obs("unknown_ns", "raw_blob", "some_noise"),  # → low_signal
    ])
    payload = project_observations_to_passport(observations, make_source_doc())

    assert payload["identity"]["ehr_code"]["value"] == "101035685"
    # low_signal obs should produce no projectable value
    assert "unknown_ns" not in payload


def test_field_value_shape_matches_frontend_contract() -> None:
    """FieldValue must have value, confidence, source, last_updated keys."""
    observations = _classify([
        make_obs("identity", "ehr_code", "101035685", page_number=1),
    ])
    payload = project_observations_to_passport(observations, make_source_doc())
    fv = payload["identity"]["ehr_code"]

    assert "value" in fv
    assert "confidence" in fv
    assert "source" in fv
    assert "last_updated" in fv
    assert fv["source"]["document_id"] == str(_FIXED_DOC_ID)
    assert fv["source"]["label"] == "EHR PDF"
    assert fv["source"]["page"] == 1
    assert fv["confidence"] == "high"


def test_missing_observations_become_null_fieldvalue() -> None:
    """Fields with no observation must produce FieldValue(value=None, confidence='low')."""
    payload = project_observations_to_passport([], make_source_doc())

    fv = payload["identity"]["ehr_code"]
    assert fv["value"] is None
    assert fv["confidence"] == "low"
    assert "source" not in fv
    assert "last_updated" not in fv


def test_multiple_observations_for_same_field_uses_latest() -> None:
    """When two observations exist for the same (namespace, key), use the newer one."""
    old_dt = datetime(2026, 5, 7, 10, 0, 0, tzinfo=timezone.utc)
    new_dt = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)

    obs_old = make_obs("identity", "ehr_code", "OLD_CODE", created_at=old_dt)
    obs_new = make_obs("identity", "ehr_code", "NEW_CODE", created_at=new_dt)
    obs_old.relevance_class = "passport_core"
    obs_new.relevance_class = "passport_core"

    payload = project_observations_to_passport([obs_old, obs_new], make_source_doc())
    assert payload["identity"]["ehr_code"]["value"] == "NEW_CODE"


def test_building_parts_projects_as_list() -> None:
    """building_parts observation → building_parts.parts is a list of BuildingPart dicts."""
    parts_data = [
        {"part_identifier": "part_1", "part_type": "Mitteeluruum",
         "part_name": "Theatre", "part_use": "Cultural", "part_area_m2": 3755.5},
    ]
    obs = make_obs("building_parts", "building_parts", parts_data, page_number=4)
    obs.relevance_class = "passport_core"

    payload = project_observations_to_passport([obs], make_source_doc())
    bp = payload["building_parts"]

    assert isinstance(bp["parts"], list)
    assert len(bp["parts"]) == 1
    part = bp["parts"][0]
    assert part["part_identifier"]["value"] == "part_1"
    assert part["part_area_m2"]["value"] == 3755.5
    assert part["part_name"]["value"] == "Theatre"
    # Each part field is a FieldValue
    for field_name in ["part_identifier", "part_type", "part_name", "part_use", "part_area_m2"]:
        assert "value" in part[field_name]
        assert "confidence" in part[field_name]


def test_floors_aggregated_from_two_observations() -> None:
    """floors.above_ground + floors.below_ground → single floors FieldValue."""
    above = make_obs("building_profile", "floors.above_ground", 4)
    below = make_obs("building_profile", "floors.below_ground", 1)
    above.relevance_class = "passport_core"
    below.relevance_class = "passport_core"

    payload = project_observations_to_passport([above, below], make_source_doc())
    floors = payload["building_profile"]["floors"]

    assert floors["value"] == {"above_ground": 4, "below_ground": 1}
    assert floors["confidence"] == "high"


def test_floors_partial_above_ground_only() -> None:
    """If only floors.above_ground is present, below_ground is None in the value."""
    above = make_obs("building_profile", "floors.above_ground", 4)
    above.relevance_class = "passport_core"

    payload = project_observations_to_passport([above], make_source_doc())
    floors = payload["building_profile"]["floors"]

    assert floors["value"]["above_ground"] == 4
    assert floors["value"]["below_ground"] is None


def test_passport_supporting_fields_are_projected() -> None:
    """passport_supporting observations (e.g. building_name) appear in the payload."""
    obs = make_obs("building_profile", "building_name", "Teatrihoone")
    obs.relevance_class = "passport_supporting"

    payload = project_observations_to_passport([obs], make_source_doc())
    assert payload["building_profile"]["building_name"]["value"] == "Teatrihoone"


def test_payload_has_required_top_level_keys() -> None:
    """Payload has schema_version, generated_at_utc, source_strategy, and all 7 sections."""
    payload = project_observations_to_passport([], make_source_doc())
    for key in [
        "schema_version", "generated_at_utc", "source_strategy",
        "identity", "building_profile", "structural_systems",
        "technical_systems", "location", "building_parts", "quality",
    ]:
        assert key in payload, f"Missing top-level key: {key}"
    assert payload["schema_version"] == "buildloop.passport.mvp.v1"
    assert payload["source_strategy"] == "ehr_pdf"


# ---------------------------------------------------------------------------
# Integration smoke test against Lai 1 golden data
# ---------------------------------------------------------------------------

def test_lai_1_golden_projection() -> None:
    """Projecting Lai 1 observations produces expected passport values."""
    assert GOLDEN_FILE_PATH.exists(), (
        f"Golden file missing: {GOLDEN_FILE_PATH}. "
        "Run the source_parsing tests first to generate it."
    )
    golden = json.loads(GOLDEN_FILE_PATH.read_text(encoding="utf-8"))

    # Build Observation instances from the golden file
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
        obs.relevance_class = entry.get("relevance_class", "unclassified")
        # Classify using the policy
        from app.services.relevance_engine.policy import classify
        obs.relevance_class = classify(obs.namespace, obs.key)
        observations.append(obs)

    payload = project_observations_to_passport(observations, make_source_doc())

    # Verify key values from the Lai 1 building
    assert payload["identity"]["ehr_code"]["value"] == "101035685"
    assert payload["identity"]["normalized_address"]["value"] == (
        "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4"
    )
    assert payload["building_profile"]["heated_area_m2"]["value"] == 4971.8
    assert payload["building_profile"]["floors"]["value"]["above_ground"] == 4
    assert len(payload["building_parts"]["parts"]) == 3

    # Structural materials present
    assert payload["structural_systems"]["foundation_type"]["value"] is not None
    assert payload["structural_systems"]["load_bearing_material"]["value"] is not None

    # Technical systems present
    assert payload["technical_systems"]["electricity"]["value"] == "võrk"
    assert payload["technical_systems"]["lift_count"]["value"] == 1
