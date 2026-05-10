"""Tests for the building_profile extractor against the real EHR PDF."""

from __future__ import annotations

import pytest

from app.services.source_parsing.extractors.building_profile import extract_building_profile
from app.services.source_parsing.page_map import build_page_map
from app.services.source_parsing.tests.conftest import FIXTURE_PDF_PATH
from app.services.source_parsing.text_extractor import extract_text


@pytest.fixture(scope="module")
def page_map() -> dict[int, str]:
    pdf_bytes = FIXTURE_PDF_PATH.read_bytes()
    extracted = extract_text(pdf_bytes)
    return build_page_map(extracted.text)


@pytest.fixture(scope="module")
def drafts(page_map: dict[int, str]) -> list:  # type: ignore[type-arg]
    return extract_building_profile(page_map)


def _get(drafts: list, key: str):  # type: ignore[no-untyped-def]
    return next((d for d in drafts if d.key == key), None)


def test_building_profile_extracts_heated_area(drafts: list) -> None:
    obs = _get(drafts, "heated_area_m2")
    assert obs is not None, "heated_area_m2 observation expected"
    assert isinstance(obs.value, float)
    assert obs.value > 0
    assert obs.unit == "m2"
    assert obs.page_number is not None


def test_building_profile_extracts_building_type(drafts: list) -> None:
    obs = _get(drafts, "building_type")
    assert obs is not None
    assert isinstance(obs.value, str)
    assert len(obs.value) > 0


def test_building_profile_extracts_building_status(drafts: list) -> None:
    obs = _get(drafts, "building_status")
    assert obs is not None
    assert isinstance(obs.value, str)


def test_building_profile_extracts_floors_above_ground(drafts: list) -> None:
    obs = _get(drafts, "floors.above_ground")
    assert obs is not None
    assert isinstance(obs.value, int)
    assert obs.value >= 1


def test_building_profile_extracts_use_categories(drafts: list) -> None:
    obs = _get(drafts, "use_categories")
    assert obs is not None
    assert isinstance(obs.value, list)
    assert len(obs.value) >= 1
    first = obs.value[0]
    assert "name" in first
    assert "area_m2" in first


def test_building_profile_uses_correct_units(drafts: list) -> None:
    for key, expected_unit in [
        ("footprint_area_m2", "m2"),
        ("heated_area_m2", "m2"),
        ("height_m", "m"),
        ("volume_m3", "m3"),
    ]:
        obs = _get(drafts, key)
        if obs is not None:  # not all PDFs have all fields
            assert obs.unit == expected_unit, f"{key}: expected unit {expected_unit}, got {obs.unit}"


def test_building_profile_all_observations_have_provenance(drafts: list) -> None:
    for d in drafts:
        has_page = d.page_number is not None
        has_evidence = d.evidence_text is not None
        assert has_page or has_evidence, (
            f"Observation {d.namespace}.{d.key} has neither page_number nor evidence_text"
        )
