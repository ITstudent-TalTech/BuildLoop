"""Tests for the technical_systems extractor against the real EHR PDF."""

from __future__ import annotations

import pytest

from app.services.source_parsing.extractors.technical_systems import extract_technical_systems
from app.services.source_parsing.page_map import build_page_map
from app.services.source_parsing.tests.conftest import FIXTURE_PDF_PATH
from app.services.source_parsing.text_extractor import extract_text


@pytest.fixture(scope="module")
def drafts() -> list:  # type: ignore[type-arg]
    pdf_bytes = FIXTURE_PDF_PATH.read_bytes()
    extracted = extract_text(pdf_bytes)
    pm = build_page_map(extracted.text)
    return extract_technical_systems(pm)


def _get(drafts: list, key: str):  # type: ignore[no-untyped-def]
    return next((d for d in drafts if d.key == key), None)


def test_technical_has_at_least_one_observation(drafts: list) -> None:
    assert len(drafts) > 0, "At least one technical_systems observation expected"


def test_technical_all_in_correct_namespace(drafts: list) -> None:
    for d in drafts:
        assert d.namespace == "technical_systems"
        assert d.section == "technical_systems"


def test_technical_lift_count_is_integer_if_present(drafts: list) -> None:
    obs = _get(drafts, "lift_count")
    if obs is not None:
        assert isinstance(obs.value, int)
        assert obs.value >= 0


def test_technical_string_fields_are_strings(drafts: list) -> None:
    string_keys = {"electricity", "water", "sewer", "heat_source", "gas", "ventilation"}
    for d in drafts:
        if d.key in string_keys:
            assert isinstance(d.value, str)
            assert len(d.value) > 0


def test_technical_all_have_provenance(drafts: list) -> None:
    for d in drafts:
        has_page = d.page_number is not None
        has_evidence = d.evidence_text is not None
        assert has_page or has_evidence, (
            f"technical_systems.{d.key} has neither page_number nor evidence_text"
        )


def test_technical_all_relevance_unclassified(drafts: list) -> None:
    for d in drafts:
        assert d.relevance_class == "unclassified"
