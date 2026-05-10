"""Tests for the location extractor against the real EHR PDF."""

from __future__ import annotations

import pytest

from app.services.source_parsing.extractors.location import extract_location
from app.services.source_parsing.page_map import build_page_map
from app.services.source_parsing.tests.conftest import FIXTURE_PDF_PATH
from app.services.source_parsing.text_extractor import extract_text


@pytest.fixture(scope="module")
def drafts() -> list:  # type: ignore[type-arg]
    pdf_bytes = FIXTURE_PDF_PATH.read_bytes()
    extracted = extract_text(pdf_bytes)
    pm = build_page_map(extracted.text)
    return extract_location(pm)


def _get(drafts: list, key: str):  # type: ignore[no-untyped-def]
    return next((d for d in drafts if d.key == key), None)


def test_location_all_in_correct_namespace(drafts: list) -> None:
    for d in drafts:
        assert d.namespace == "location"
        assert d.section == "location"


def test_location_coordinates_if_present(drafts: list) -> None:
    obs = _get(drafts, "coordinates")
    if obs is None:
        pytest.skip("No coordinates found in this PDF — check geometry block")
    assert isinstance(obs.value, list)
    assert len(obs.value) > 0
    # Each coordinate pair has 'y' and 'x' float keys
    for coord in obs.value:
        assert "y" in coord and "x" in coord
        assert isinstance(coord["y"], float)
        assert isinstance(coord["x"], float)


def test_location_geometry_method_if_present(drafts: list) -> None:
    obs = _get(drafts, "geometry_method")
    if obs is not None:
        assert isinstance(obs.value, str)
        assert len(obs.value) > 0


def test_location_shape_type_if_present(drafts: list) -> None:
    obs = _get(drafts, "shape_type")
    if obs is not None:
        assert isinstance(obs.value, str)


def test_location_all_have_provenance(drafts: list) -> None:
    for d in drafts:
        has_page = d.page_number is not None
        has_evidence = d.evidence_text is not None
        assert has_page or has_evidence, (
            f"location.{d.key} has neither page_number nor evidence_text"
        )


def test_location_all_on_same_page(drafts: list) -> None:
    """geometry_method, shape_type, coordinates should all be on the same page."""
    pages = {d.page_number for d in drafts if d.page_number is not None}
    assert len(pages) <= 1, (
        f"Location observations span multiple pages: {pages}. "
        "They should all come from the same geometry block."
    )
