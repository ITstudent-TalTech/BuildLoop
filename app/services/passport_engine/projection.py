"""project_observations_to_passport — pure projection function.

Takes classified Observation rows and returns a payload_json dict that
matches the FieldValue<T> shape the frontend expects (web/lib/api/types.ts).

Only observations classified as 'passport_core' or 'passport_supporting'
are projected.  'low_signal', 'listing_candidate', and 'excluded' are ignored.

When multiple observations exist for the same field (e.g. re-runs), the
most recent one (highest created_at) is used.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.models.observations import Observation
from app.models.source_documents import SourceDocument

# Buckets that are projected into the passport
_PROJECTED_BUCKETS = frozenset({"passport_core", "passport_supporting"})

# Canonical section → ordered field list for quality scoring.
# Defines both the projection structure AND the completeness denominator.
CANONICAL_FIELDS: dict[str, list[str]] = {
    "identity": [
        "ehr_code", "normalized_address", "address_aliases", "country", "input_address",
    ],
    "building_profile": [
        "building_type", "building_status", "building_name", "use_categories",
        "floors",  # special: aggregated from floors.above_ground + floors.below_ground
        "footprint_area_m2", "heated_area_m2", "net_area_m2", "public_use_area_m2",
        "technical_area_m2", "height_m", "length_m", "width_m", "depth_m", "volume_m3",
    ],
    "structural_systems": [
        "foundation_type", "load_bearing_material", "wall_type",
        "facade_finish_material", "floor_structure_material",
        "roof_structure_material", "roof_covering_material",
    ],
    "technical_systems": [
        "electricity", "water", "sewer", "heat_source", "gas", "ventilation", "lift_count",
    ],
    "location": [
        "geometry_method", "shape_type", "coordinates",
    ],
    "building_parts": [
        "parts",  # the entire parts list is one logical field
    ],
}


# ---------------------------------------------------------------------------
# FieldValue helpers
# ---------------------------------------------------------------------------

def _null_field_value() -> dict[str, Any]:
    """FieldValue for a field with no matching observation."""
    return {"value": None, "confidence": "low"}


def _field_value_from_obs(obs: Observation, doc_id: str) -> dict[str, Any]:
    """FieldValue populated from a single Observation row."""
    fv: dict[str, Any] = {
        "value": obs.value_json,
        "confidence": obs.confidence_label or "low",
        "source": {
            "document_id": doc_id,
            "page": obs.page_number,
            "label": "EHR PDF",
        },
        "last_updated": obs.created_at.isoformat() if obs.created_at else None,
    }
    if obs.unit is not None:
        fv["unit"] = obs.unit
    return fv


def _most_recent(observations: list[Observation]) -> Observation:
    """Return the observation with the latest created_at."""
    return max(
        observations,
        key=lambda o: o.created_at or datetime.min.replace(tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# Building-parts projection
# ---------------------------------------------------------------------------

def _project_building_parts(
    parts_obs: Observation | None, doc_id: str
) -> dict[str, Any]:
    """Project the building_parts observation into the passport shape.

    Each raw part dict becomes a BuildingPart with FieldValues.  All sub-fields
    share the confidence and source of the containing observation.
    """
    if parts_obs is None:
        return {
            "parts": [],
            "confidence": "low",
            "source": None,
        }

    raw_parts: list[dict[str, Any]] = parts_obs.value_json  # type: ignore[assignment]
    if not isinstance(raw_parts, list):
        raw_parts = []

    conf: str = parts_obs.confidence_label or "low"
    source: dict[str, Any] = {
        "document_id": doc_id,
        "page": parts_obs.page_number,
        "label": "EHR PDF",
    }
    last_updated: str | None = (
        parts_obs.created_at.isoformat() if parts_obs.created_at else None
    )

    def _part_fv(value: Any, unit: str | None = None) -> dict[str, Any]:
        fv: dict[str, Any] = {
            "value": value,
            "confidence": conf,
            "source": source,
            "last_updated": last_updated,
        }
        if unit is not None:
            fv["unit"] = unit
        return fv

    parts: list[dict[str, Any]] = []
    for part in raw_parts:
        parts.append({
            "part_identifier": _part_fv(part.get("part_identifier")),
            "part_type":       _part_fv(part.get("part_type")),
            "part_name":       _part_fv(part.get("part_name")),
            "part_use":        _part_fv(part.get("part_use")),
            "part_area_m2":    _part_fv(part.get("part_area_m2")),
        })

    return {
        "parts": parts,
        "confidence": conf,
        "source": source,
    }


# ---------------------------------------------------------------------------
# Floors aggregation
# ---------------------------------------------------------------------------

def _project_floors(
    above_obs: Observation | None,
    below_obs: Observation | None,
    doc_id: str,
) -> dict[str, Any]:
    """Combine floors.above_ground + floors.below_ground into a single FieldValue."""
    if above_obs is None and below_obs is None:
        return _null_field_value()

    # Metadata from the more recent observation
    base = _most_recent([o for o in [above_obs, below_obs] if o is not None])

    return {
        "value": {
            "above_ground": above_obs.value_json if above_obs is not None else None,
            "below_ground": below_obs.value_json if below_obs is not None else None,
        },
        "confidence": base.confidence_label or "low",
        "source": {
            "document_id": doc_id,
            "page": base.page_number,
            "label": "EHR PDF",
        },
        "last_updated": base.created_at.isoformat() if base.created_at else None,
    }


# ---------------------------------------------------------------------------
# Main projection function
# ---------------------------------------------------------------------------

def project_observations_to_passport(
    observations: list[Observation],
    source_document: SourceDocument | None,
    schema_version: str = "buildloop.passport.mvp.v1",
) -> dict[str, Any]:
    """Project classified observations into a passport payload_json.

    Inputs:
      observations    — list of Observation ORM rows (any relevance_class).
      source_document — the SourceDocument the observations came from.
      schema_version  — semver stamped on the payload.
    Outputs:
      dict matching the FieldValue<T>-shaped PassportDraft from types.ts.
      Quality section is present but scores are 0; caller must populate via
      quality.py functions after receiving this return value.
    Side effects:
      None — pure function, no DB writes.
    """
    doc_id: str = str(source_document.id) if source_document else "unknown"

    # Filter to projectable buckets only
    relevant = [
        o for o in observations if o.relevance_class in _PROJECTED_BUCKETS
    ]

    # Build (namespace, key) → most recent observation index
    obs_index: dict[tuple[str, str], Observation] = {}
    for obs in relevant:
        key_tuple = (obs.namespace, obs.key)
        existing = obs_index.get(key_tuple)
        if existing is None:
            obs_index[key_tuple] = obs
        else:
            obs_index[key_tuple] = _most_recent([existing, obs])

    def _get(namespace: str, key: str) -> Observation | None:
        return obs_index.get((namespace, key))

    def _fv(namespace: str, key: str) -> dict[str, Any]:
        obs = _get(namespace, key)
        return _field_value_from_obs(obs, doc_id) if obs else _null_field_value()

    # ── Identity ────────────────────────────────────────────────────────
    identity: dict[str, Any] = {
        "ehr_code":           _fv("identity", "ehr_code"),
        "normalized_address": _fv("identity", "normalized_address"),
        "address_aliases":    _fv("identity", "address_aliases"),
        "country":            _fv("identity", "country"),
        "input_address":      _fv("identity", "input_address"),
    }

    # ── Building profile ────────────────────────────────────────────────
    building_profile: dict[str, Any] = {
        "building_type":     _fv("building_profile", "building_type"),
        "building_status":   _fv("building_profile", "building_status"),
        "building_name":     _fv("building_profile", "building_name"),
        "use_categories":    _fv("building_profile", "use_categories"),
        "floors":            _project_floors(
                                 _get("building_profile", "floors.above_ground"),
                                 _get("building_profile", "floors.below_ground"),
                                 doc_id,
                             ),
        "footprint_area_m2": _fv("building_profile", "footprint_area_m2"),
        "heated_area_m2":    _fv("building_profile", "heated_area_m2"),
        "net_area_m2":       _fv("building_profile", "net_area_m2"),
        "public_use_area_m2":_fv("building_profile", "public_use_area_m2"),
        "technical_area_m2": _fv("building_profile", "technical_area_m2"),
        "height_m":          _fv("building_profile", "height_m"),
        "length_m":          _fv("building_profile", "length_m"),
        "width_m":           _fv("building_profile", "width_m"),
        "depth_m":           _fv("building_profile", "depth_m"),
        "volume_m3":         _fv("building_profile", "volume_m3"),
    }

    # ── Structural systems ──────────────────────────────────────────────
    structural_systems: dict[str, Any] = {
        "foundation_type":          _fv("structural_systems", "foundation_type"),
        "load_bearing_material":    _fv("structural_systems", "load_bearing_material"),
        "wall_type":                _fv("structural_systems", "wall_type"),
        "facade_finish_material":   _fv("structural_systems", "facade_finish_material"),
        "floor_structure_material": _fv("structural_systems", "floor_structure_material"),
        "roof_structure_material":  _fv("structural_systems", "roof_structure_material"),
        "roof_covering_material":   _fv("structural_systems", "roof_covering_material"),
    }

    # ── Technical systems ───────────────────────────────────────────────
    technical_systems: dict[str, Any] = {
        "electricity": _fv("technical_systems", "electricity"),
        "water":       _fv("technical_systems", "water"),
        "sewer":       _fv("technical_systems", "sewer"),
        "heat_source": _fv("technical_systems", "heat_source"),
        "gas":         _fv("technical_systems", "gas"),
        "ventilation": _fv("technical_systems", "ventilation"),
        "lift_count":  _fv("technical_systems", "lift_count"),
    }

    # ── Location ────────────────────────────────────────────────────────
    location: dict[str, Any] = {
        "geometry_method": _fv("location", "geometry_method"),
        "shape_type":      _fv("location", "shape_type"),
        "coordinates":     _fv("location", "coordinates"),
    }

    # ── Building parts ───────────────────────────────────────────────────
    building_parts = _project_building_parts(
        _get("building_parts", "building_parts"), doc_id
    )

    return {
        "schema_version":   schema_version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_strategy":  "ehr_pdf",
        "identity":             identity,
        "building_profile":     building_profile,
        "structural_systems":   structural_systems,
        "technical_systems":    technical_systems,
        "location":             location,
        "building_parts":       building_parts,
        "quality": {
            "schema_completeness_score": 0.0,
            "confidence_score":          0.0,
            "confidence_label":          "low",
            "section_breakdown":         {},
            "missing_fields":            [],
        },
    }
