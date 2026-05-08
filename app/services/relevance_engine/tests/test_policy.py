"""Tests for the static relevance policy.

Verifies that:
  - every canonical key maps to the expected bucket per doc 05
  - unknown keys default to 'low_signal'
"""

from __future__ import annotations

import pytest

from app.services.relevance_engine.policy import (
    DEFAULT_BUCKET,
    FIELD_RELEVANCE_MAP,
    classify,
)


# ---------------------------------------------------------------------------
# Known key → expected bucket (representative sample per doc 05 section)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("namespace,key,expected_bucket", [
    # Identity — all passport_core
    ("identity", "ehr_code",            "passport_core"),
    ("identity", "normalized_address",  "passport_core"),
    ("identity", "address_aliases",     "passport_core"),
    ("identity", "country",             "passport_core"),
    ("identity", "input_address",       "passport_core"),
    # Building profile — core
    ("building_profile", "building_type",        "passport_core"),
    ("building_profile", "building_status",      "passport_core"),
    ("building_profile", "use_categories",       "passport_core"),
    ("building_profile", "floors.above_ground",  "passport_core"),
    ("building_profile", "floors.below_ground",  "passport_core"),
    ("building_profile", "footprint_area_m2",    "passport_core"),
    ("building_profile", "heated_area_m2",       "passport_core"),
    ("building_profile", "net_area_m2",          "passport_core"),
    ("building_profile", "height_m",             "passport_core"),
    ("building_profile", "volume_m3",            "passport_core"),
    # Building profile — supporting
    ("building_profile", "building_name",      "passport_supporting"),
    ("building_profile", "public_use_area_m2", "passport_supporting"),
    ("building_profile", "technical_area_m2",  "passport_supporting"),
    ("building_profile", "length_m",           "passport_supporting"),
    ("building_profile", "width_m",            "passport_supporting"),
    ("building_profile", "depth_m",            "passport_supporting"),
    # Structural systems — all passport_core
    ("structural_systems", "foundation_type",          "passport_core"),
    ("structural_systems", "load_bearing_material",    "passport_core"),
    ("structural_systems", "wall_type",                "passport_core"),
    ("structural_systems", "facade_finish_material",   "passport_core"),
    ("structural_systems", "floor_structure_material", "passport_core"),
    ("structural_systems", "roof_structure_material",  "passport_core"),
    ("structural_systems", "roof_covering_material",   "passport_core"),
    # Technical systems — all passport_core
    ("technical_systems", "electricity", "passport_core"),
    ("technical_systems", "water",       "passport_core"),
    ("technical_systems", "sewer",       "passport_core"),
    ("technical_systems", "heat_source", "passport_core"),
    ("technical_systems", "gas",         "passport_core"),
    ("technical_systems", "ventilation", "passport_core"),
    ("technical_systems", "lift_count",  "passport_core"),
    # Location — all passport_core
    ("location", "geometry_method", "passport_core"),
    ("location", "shape_type",      "passport_core"),
    ("location", "coordinates",     "passport_core"),
    # Building parts — passport_core (primary)
    ("building_parts", "building_parts", "passport_core"),
])
def test_known_keys_classify_correctly(
    namespace: str, key: str, expected_bucket: str
) -> None:
    assert classify(namespace, key) == expected_bucket, (
        f"{namespace}.{key} → expected '{expected_bucket}', "
        f"got '{classify(namespace, key)}'"
    )


def test_unknown_key_defaults_to_low_signal() -> None:
    assert classify("identity", "nonexistent_field") == DEFAULT_BUCKET
    assert classify("unknown_namespace", "any_key") == DEFAULT_BUCKET
    assert classify("building_profile", "raw_ehr_blob") == DEFAULT_BUCKET


def test_field_relevance_map_contains_all_canonical_keys() -> None:
    """Every key listed in the task card is present in the map."""
    expected_keys = {
        # identity
        "identity.ehr_code", "identity.normalized_address",
        "identity.address_aliases", "identity.country", "identity.input_address",
        # building_profile core
        "building_profile.building_type", "building_profile.building_status",
        "building_profile.use_categories",
        "building_profile.floors.above_ground", "building_profile.floors.below_ground",
        "building_profile.footprint_area_m2", "building_profile.heated_area_m2",
        "building_profile.net_area_m2", "building_profile.height_m",
        "building_profile.volume_m3",
        # building_profile supporting
        "building_profile.building_name", "building_profile.public_use_area_m2",
        "building_profile.technical_area_m2", "building_profile.length_m",
        "building_profile.width_m", "building_profile.depth_m",
        # structural_systems
        "structural_systems.foundation_type", "structural_systems.load_bearing_material",
        "structural_systems.wall_type", "structural_systems.facade_finish_material",
        "structural_systems.floor_structure_material",
        "structural_systems.roof_structure_material",
        "structural_systems.roof_covering_material",
        # technical_systems
        "technical_systems.electricity", "technical_systems.water",
        "technical_systems.sewer", "technical_systems.heat_source",
        "technical_systems.gas", "technical_systems.ventilation",
        "technical_systems.lift_count",
        # location
        "location.geometry_method", "location.shape_type", "location.coordinates",
        # building_parts
        "building_parts.building_parts",
    }
    missing = expected_keys - set(FIELD_RELEVANCE_MAP.keys())
    assert not missing, f"Keys missing from FIELD_RELEVANCE_MAP: {sorted(missing)}"
