"""Tests for the identity extractor against the real EHR PDF."""

from __future__ import annotations

import pytest

from app.services.source_parsing.extractors.identity import extract_identity
from app.services.source_parsing.page_map import build_page_map
from app.services.source_parsing.tests.conftest import FIXTURE_PDF_PATH
from app.services.source_parsing.text_extractor import extract_text


@pytest.fixture(scope="module")
def page_map() -> dict[int, str]:
    pdf_bytes = FIXTURE_PDF_PATH.read_bytes()
    extracted = extract_text(pdf_bytes)
    return build_page_map(extracted.text)


def test_identity_extractor_finds_ehr_code(page_map: dict[int, str]) -> None:
    drafts = extract_identity(page_map)
    ehr = next((d for d in drafts if d.key == "ehr_code"), None)
    assert ehr is not None, "ehr_code observation expected"
    assert ehr.namespace == "identity"
    assert ehr.section == "identity"
    assert ehr.value is not None
    # Lai 1 has EHR code 101035685
    assert str(ehr.value) == "101035685"
    assert ehr.page_number is not None


def test_identity_extractor_finds_normalized_address(page_map: dict[int, str]) -> None:
    drafts = extract_identity(page_map)
    addr = next((d for d in drafts if d.key == "normalized_address"), None)
    assert addr is not None
    assert isinstance(addr.value, str)
    assert len(addr.value) > 5
    assert addr.page_number is not None


def test_identity_extractor_emits_country_ee(page_map: dict[int, str]) -> None:
    drafts = extract_identity(page_map)
    country = next((d for d in drafts if d.key == "country"), None)
    assert country is not None
    assert country.value == "EE"


def test_identity_extractor_emits_input_address_when_provided(page_map: dict[int, str]) -> None:
    drafts = extract_identity(page_map, address_input="Lai 1, Tallinn")
    inp = next((d for d in drafts if d.key == "input_address"), None)
    assert inp is not None
    assert inp.value == "Lai 1, Tallinn"


def test_identity_extractor_no_input_address_by_default(page_map: dict[int, str]) -> None:
    drafts = extract_identity(page_map)
    inp = next((d for d in drafts if d.key == "input_address"), None)
    assert inp is None


def test_identity_observations_have_provenance(page_map: dict[int, str]) -> None:
    drafts = extract_identity(page_map)
    pdf_observations = [d for d in drafts if d.key in ("ehr_code", "normalized_address")]
    for d in pdf_observations:
        has_page = d.page_number is not None
        has_evidence = d.evidence_text is not None
        assert has_page or has_evidence, (
            f"Observation {d.namespace}.{d.key} has neither page_number nor evidence_text"
        )
