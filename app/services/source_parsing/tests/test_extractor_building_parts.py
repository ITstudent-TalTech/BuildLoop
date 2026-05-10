"""Tests for the building_parts extractor against the real EHR PDF."""

from __future__ import annotations

import pytest

from app.services.source_parsing.extractors.building_parts import (
    extract_building_parts,
    parse_building_parts,
)
from app.services.source_parsing.tests.conftest import FIXTURE_PDF_PATH
from app.services.source_parsing.text_extractor import extract_text


@pytest.fixture(scope="module")
def full_text() -> str:
    pdf_bytes = FIXTURE_PDF_PATH.read_bytes()
    return extract_text(pdf_bytes).text


@pytest.fixture(scope="module")
def parts_drafts(full_text: str) -> list:  # type: ignore[type-arg]
    return extract_building_parts(full_text)


def test_building_parts_found_in_canonical_pdf(parts_drafts: list) -> None:
    assert len(parts_drafts) > 0, (
        "Expected at least one building_parts observation from Lai 1 EHR PDF"
    )


def test_building_parts_single_observation_with_list_value(parts_drafts: list) -> None:
    # The extractor emits one observation whose value is the full parts list
    assert len(parts_drafts) == 1
    obs = parts_drafts[0]
    assert obs.namespace == "building_parts"
    assert obs.key == "building_parts"
    assert isinstance(obs.value, list)
    assert len(obs.value) >= 1


def test_building_parts_each_part_has_identifier(parts_drafts: list) -> None:
    parts = parts_drafts[0].value
    for part in parts:
        assert "part_identifier" in part
        assert part["part_identifier"].startswith("part_")


def test_building_parts_each_part_has_source_pdf(parts_drafts: list) -> None:
    parts = parts_drafts[0].value
    for part in parts:
        assert part.get("source") == "pdf"


def test_building_parts_page_number_is_4(parts_drafts: list) -> None:
    # Reference script hardcodes page 4 for building_parts
    assert parts_drafts[0].page_number == 4


def test_building_parts_has_evidence_text(parts_drafts: list) -> None:
    assert parts_drafts[0].evidence_text is not None


def test_parse_building_parts_synthetic_text() -> None:
    """Unit test for parse_building_parts with synthetic Estonian-format text."""
    synthetic = (
        "Ehitise osad\n"
        "Osa nr Näitaja EHR andmed\n"
        "Ehitise osa tüüp Eluruum Sissepääsu korrus 1\n"
        "Ehitise kuju, kus hooneosa asub 1\n"
        "Ehitise osa nimetus Korter Kasutamise otstarve Eluruum\n"
        "Hooneosa aadress some address\n"
        "Ehitise osa pind (m2) 50,00\n"
        "Kokku \n"
    )
    parts = parse_building_parts(synthetic)
    assert len(parts) == 1
    assert parts[0]["part_identifier"] == "part_1"
    assert parts[0]["part_type"] == "Eluruum"
    assert parts[0]["part_area_m2"] == pytest.approx(50.0)
