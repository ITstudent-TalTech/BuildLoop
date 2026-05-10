"""PDF text extraction — pypdf primary, pdfplumber fallback.

Decision locked: pypdf primary / pdfplumber fallback per DECISIONS.md.
Adapted from extract_text_from_pdf() in buildloop_passport_from_address.py
(line 406) to accept raw bytes instead of a file path.

The page separator sentinel "---PAGE---" is preserved exactly as in the script
so that build_page_map() works unchanged.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field


@dataclass
class ExtractedText:
    """Result of one PDF text extraction attempt."""

    text: str
    """Full document text, pages joined with '\\n---PAGE---\\n'."""

    pages: dict[int, str] = field(default_factory=dict)
    """Per-page text: {1: page1_text, 2: page2_text, ...}"""

    method: str = "pypdf"
    """'pypdf' | 'pdfplumber' — which library succeeded."""

    page_count: int = 0


def extract_text(pdf_bytes: bytes) -> ExtractedText:
    """Extract text from PDF bytes using pypdf, falling back to pdfplumber.

    Inputs:
      pdf_bytes — raw PDF file contents.
    Outputs:
      ExtractedText with full text, per-page dict, method, and page_count.
    Raises:
      RuntimeError if both libraries fail to extract any text.
    """
    # --- Primary: pypdf ---
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages: dict[int, str] = {}
        for i, page in enumerate(reader.pages):
            pages[i + 1] = page.extract_text() or ""
        text = "\n---PAGE---\n".join(pages[i] for i in sorted(pages))
        if text.strip():
            return ExtractedText(
                text=text,
                pages=pages,
                method="pypdf",
                page_count=len(pages),
            )
    except Exception:
        pass

    # --- Fallback: pdfplumber ---
    try:
        import pdfplumber  # type: ignore[import-untyped]

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            fb_pages: dict[int, str] = {}
            for i, plumber_page in enumerate(pdf.pages):
                fb_pages[i + 1] = plumber_page.extract_text() or ""
            text = "\n---PAGE---\n".join(fb_pages[i] for i in sorted(fb_pages))
            if text.strip():
                return ExtractedText(
                    text=text,
                    pages=fb_pages,
                    method="pdfplumber",
                    page_count=len(fb_pages),
                )
    except Exception:
        pass

    raise RuntimeError(
        "Could not extract text from PDF. "
        "Both pypdf and pdfplumber failed to produce any text. "
        "Ensure the file is a valid, text-based PDF."
    )
