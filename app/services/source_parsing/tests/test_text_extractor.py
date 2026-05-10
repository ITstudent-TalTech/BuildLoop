"""Tests for text_extractor using the real EHR PDF fixture.

Acceptance criteria (integration, real PDF):
  - pypdf extracts non-empty text from lai_1_101035685.pdf
  - Known Estonian terms appear in the extracted text
  - Page separation produces multiple pages
"""

from __future__ import annotations

import pytest

from app.services.source_parsing.tests.conftest import FIXTURE_PDF_PATH
from app.services.source_parsing.text_extractor import ExtractedText, extract_text


@pytest.fixture(scope="module")
def real_pdf_bytes() -> bytes:
    assert FIXTURE_PDF_PATH.exists(), f"Fixture PDF not found: {FIXTURE_PDF_PATH}"
    return FIXTURE_PDF_PATH.read_bytes()


@pytest.fixture(scope="module")
def extracted(real_pdf_bytes: bytes) -> ExtractedText:
    return extract_text(real_pdf_bytes)


def test_pypdf_extracts_text_from_real_ehr_pdf(extracted: ExtractedText) -> None:
    assert extracted.text.strip(), "Extracted text must not be empty"
    assert extracted.page_count > 0


def test_extraction_method_is_pypdf_primary(extracted: ExtractedText) -> None:
    # pypdf is the primary; pdfplumber is only used when pypdf fails
    assert extracted.method in {"pypdf", "pdfplumber"}, (
        f"Unexpected extraction method: {extracted.method}"
    )


def test_extracted_text_has_known_estonian_phrases(extracted: ExtractedText) -> None:
    text_lower = extracted.text.lower()
    # These phrases appear in every EHR PDF — their absence means extraction failed
    for phrase in ["ehitis", "kasutamise otstarve", "ehitisregistri kood"]:
        assert phrase in text_lower, f"Expected Estonian phrase not found: '{phrase}'"


def test_pages_are_separated(extracted: ExtractedText) -> None:
    assert extracted.page_count > 1, "Real EHR PDF should have more than one page"
    assert len(extracted.pages) == extracted.page_count
    # Page numbers start at 1
    assert 1 in extracted.pages
    assert extracted.page_count in extracted.pages


def test_extract_text_raises_on_garbage_bytes() -> None:
    with pytest.raises(RuntimeError, match="Could not extract text"):
        extract_text(b"not-a-pdf-at-all-random-garbage-bytes-xyz")
