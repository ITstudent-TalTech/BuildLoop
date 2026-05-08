"""Quality scoring for passport drafts.

All functions are pure — no DB access.  The service layer calls these
after project_observations_to_passport() and updates the quality section
of the payload before persisting.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.models.observations import Observation
from app.services.passport_engine.projection import CANONICAL_FIELDS

# Static label → weight mapping for section confidence derivation.
# Mirrors settings defaults so section_breakdown doesn't need Settings injected.
_LABEL_TO_WEIGHT: dict[str, float] = {
    "high":   0.95,
    "medium": 0.70,
    "low":    0.40,
}
_DEFAULT_WEIGHT = 0.50


def _label_to_weight(label: str | None) -> float:
    if label is None:
        return _DEFAULT_WEIGHT
    return _LABEL_TO_WEIGHT.get(label, _DEFAULT_WEIGHT)


def _weight_to_label(avg_weight: float) -> str:
    if avg_weight >= 0.90:
        return "high"
    if avg_weight >= 0.60:
        return "medium"
    return "low"


def confidence_weight(label: str | None, settings: Settings) -> float:
    """Map a confidence_label to its numeric weight via Settings."""
    if label == "high":
        return settings.passport_confidence_weight_high
    if label == "medium":
        return settings.passport_confidence_weight_medium
    if label == "low":
        return settings.passport_confidence_weight_low
    return settings.passport_confidence_weight_default


# ---------------------------------------------------------------------------
# Field-presence helpers
# ---------------------------------------------------------------------------

def _is_populated(section: str, field: str, payload: dict[str, Any]) -> bool:
    """Return True if the field has a non-null FieldValue.value in the payload."""
    if section == "building_parts":
        return bool(payload.get("building_parts", {}).get("parts"))
    section_data = payload.get(section, {})
    fv = section_data.get(field)
    if not isinstance(fv, dict):
        return False
    return fv.get("value") is not None


def _field_confidence(section: str, field: str, payload: dict[str, Any]) -> str | None:
    """Return the confidence label of a populated FieldValue, or None."""
    if section == "building_parts":
        return payload.get("building_parts", {}).get("confidence")
    fv = payload.get(section, {}).get(field)
    if not isinstance(fv, dict) or fv.get("value") is None:
        return None
    return fv.get("confidence")


# ---------------------------------------------------------------------------
# Public scoring functions
# ---------------------------------------------------------------------------

def compute_schema_completeness(payload: dict[str, Any]) -> float:
    """Return 0-100: (populated fields / total expected fields) × 100.

    Uses CANONICAL_FIELDS as the total.  'floors' counts as one logical
    field (populated if value is not None).
    """
    total = 0
    populated = 0
    for section, fields in CANONICAL_FIELDS.items():
        for field in fields:
            total += 1
            if _is_populated(section, field, payload):
                populated += 1
    return round((populated / total) * 100, 1) if total > 0 else 0.0


def compute_confidence_score(
    observations: list[Observation],
    settings: Settings,
) -> float:
    """Return 0-100: weighted average of confidence labels × 100.

    Inputs:
      observations — only passport_core + passport_supporting observations
                     should be passed; caller filters.
      settings     — used for tunable weight values.
    """
    if not observations:
        return 0.0
    total_weight = sum(
        confidence_weight(o.confidence_label, settings) for o in observations
    )
    return round((total_weight / len(observations)) * 100, 1)


def derive_section_breakdown(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return per-section stats: fields_populated, fields_total, confidence_label.

    The confidence_label for a section is derived from the confidence labels
    of its populated FieldValues, weighted by _LABEL_TO_WEIGHT.
    """
    breakdown: dict[str, dict[str, Any]] = {}

    for section, fields in CANONICAL_FIELDS.items():
        total = len(fields)
        populated = 0
        conf_weights: list[float] = []

        for field in fields:
            if _is_populated(section, field, payload):
                populated += 1
                conf = _field_confidence(section, field, payload)
                conf_weights.append(_label_to_weight(conf))

        avg = sum(conf_weights) / len(conf_weights) if conf_weights else 0.0
        breakdown[section] = {
            "fields_populated":  populated,
            "fields_total":      total,
            "confidence_label":  _weight_to_label(avg),
        }

    return breakdown


def list_missing_fields(payload: dict[str, Any]) -> list[str]:
    """Return list of '<section>.<field>' paths where FieldValue.value is null."""
    missing: list[str] = []
    for section, fields in CANONICAL_FIELDS.items():
        for field in fields:
            if not _is_populated(section, field, payload):
                missing.append(f"{section}.{field}")
    return missing
