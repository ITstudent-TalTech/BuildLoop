"""Static field-to-bucket relevance policy.

FIELD_RELEVANCE_MAP is the single source of truth for which
`<namespace>.<key>` maps to which relevance bucket.  It is sourced from
doc 05's "Practical field policy" section and is a deliberate design
choice: classification is a hard-coded policy, not a learned model.
Adding a new field requires a code change.  See DECISIONS.md.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Policy map  —  <namespace>.<key> → bucket
# ---------------------------------------------------------------------------

FIELD_RELEVANCE_MAP: dict[str, str] = {
    # ── Identity (all passport_core) ────────────────────────────────────
    "identity.ehr_code":            "passport_core",
    "identity.normalized_address":  "passport_core",
    "identity.address_aliases":     "passport_core",
    "identity.country":             "passport_core",
    "identity.input_address":       "passport_core",

    # ── Building profile — core ──────────────────────────────────────────
    "building_profile.building_type":       "passport_core",
    "building_profile.building_status":     "passport_core",
    "building_profile.use_categories":      "passport_core",
    "building_profile.floors.above_ground": "passport_core",
    "building_profile.floors.below_ground": "passport_core",
    "building_profile.footprint_area_m2":   "passport_core",
    "building_profile.heated_area_m2":      "passport_core",
    "building_profile.net_area_m2":         "passport_core",
    "building_profile.height_m":            "passport_core",
    "building_profile.volume_m3":           "passport_core",

    # ── Building profile — supporting ───────────────────────────────────
    "building_profile.building_name":      "passport_supporting",
    "building_profile.public_use_area_m2": "passport_supporting",
    "building_profile.technical_area_m2":  "passport_supporting",
    "building_profile.length_m":           "passport_supporting",
    "building_profile.width_m":            "passport_supporting",
    "building_profile.depth_m":            "passport_supporting",

    # ── Structural systems (all passport_core) ───────────────────────────
    "structural_systems.foundation_type":         "passport_core",
    "structural_systems.load_bearing_material":   "passport_core",
    "structural_systems.wall_type":               "passport_core",
    "structural_systems.facade_finish_material":  "passport_core",
    "structural_systems.floor_structure_material":"passport_core",
    "structural_systems.roof_structure_material": "passport_core",
    "structural_systems.roof_covering_material":  "passport_core",

    # ── Technical systems (all passport_core) ────────────────────────────
    "technical_systems.electricity":  "passport_core",
    "technical_systems.water":        "passport_core",
    "technical_systems.sewer":        "passport_core",
    "technical_systems.heat_source":  "passport_core",
    "technical_systems.gas":          "passport_core",
    "technical_systems.ventilation":  "passport_core",
    "technical_systems.lift_count":   "passport_core",

    # ── Location (all passport_core) ─────────────────────────────────────
    "location.geometry_method": "passport_core",
    "location.shape_type":      "passport_core",
    "location.coordinates":     "passport_core",

    # ── Building parts (passport_core primary) ───────────────────────────
    # Listing candidate derivation in Track 2.8 reads observations by
    # namespace='building_parts' directly, not by a secondary classification.
    # See DECISIONS.md §"Single bucket per observation".
    "building_parts.building_parts": "passport_core",
}

DEFAULT_BUCKET: str = "low_signal"


def classify(namespace: str, key: str) -> str:
    """Return the relevance bucket for a single observation.

    Inputs:
      namespace — observation namespace (e.g. 'building_profile').
      key       — observation key (e.g. 'heated_area_m2').
    Outputs:
      One of 'passport_core' | 'passport_supporting' | 'listing_candidate'
      | 'low_signal' | 'excluded'.  Unknown keys default to 'low_signal'.
    """
    return FIELD_RELEVANCE_MAP.get(f"{namespace}.{key}", DEFAULT_BUCKET)
