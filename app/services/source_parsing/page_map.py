"""Page map utilities — verbatim from buildloop_passport_from_address.py (lines 449-465).

Also hosts normalize_multiline_value and parse_decimal (lines 99-115 of the script)
since they are used by find_with_page and by the extractors.

DO NOT alter these functions without auditing against the reference script.
The regex patterns and whitespace-normalisation logic are hand-tuned for real
Estonian EHR PDFs and must be preserved exactly.
"""

from __future__ import annotations

import re
from typing import Optional


def normalize_multiline_value(s: Optional[str]) -> Optional[str]:
    """Collapse multi-line whitespace and non-breaking spaces to a single space.

    Lifted verbatim from normalize_multiline_value() in the script (line 99).
    """
    if s is None:
        return None
    s = s.replace(" ", " ")
    s = re.sub(r"\s*\n\s*", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip() or None


def parse_decimal(value: Optional[str]) -> Optional[float]:
    """Parse an Estonian-formatted decimal string (comma separator, space thousands).

    Lifted verbatim from parse_decimal() in the script (line 108).
    Examples: "1 648,00" → 1648.0, "12,5" → 12.5
    """
    if value is None:
        return None
    v = value.replace(" ", " ").replace(" ", "").replace(",", ".")
    try:
        return float(v)
    except Exception:
        return None


def build_page_map(text: str) -> dict[int, str]:
    """Split full document text into {page_number: page_text} dict.

    Lifted verbatim from build_page_map() in the script (line 449).
    Pages are separated by the sentinel "---PAGE---" inserted by extract_text().
    """
    if "---PAGE---" not in text:
        return {1: text}
    return {i + 1: part for i, part in enumerate(text.split("---PAGE---"))}


def find_with_page(
    pattern: str,
    page_map: dict[int, str],
    flags: int = 0,
) -> tuple[str | None, int | None, str | None]:
    """Search all pages for a regex pattern, return (value, page_number, evidence).

    Lifted verbatim from find_with_page() in the script (line 455).
    Returns the first match found scanning pages in ascending order.
    Group 1 of the pattern is the extracted value; group 0 is the evidence.
    """
    for page_no, page_text in page_map.items():
        m = re.search(pattern, page_text, flags)
        if m:
            return (
                normalize_multiline_value(m.group(1)),
                page_no,
                normalize_multiline_value(m.group(0)),
            )
    return None, None, None


def find_first(pattern: str, text: str, flags: int = 0) -> str | None:
    """Return normalised group(1) of first match, or None.

    Lifted verbatim from find_first() in the script (line 463).
    """
    m = re.search(pattern, text, flags)
    return normalize_multiline_value(m.group(1)) if m else None
