"""Building parts namespace extractor.

Produces one observation:
  building_parts / building_parts — the full list of part dicts

This follows the script's approach: one observation with the entire parts
list as value_json, per the first option listed in doc 03 ("building_parts").
The page is hardcoded to 4 per the reference script's add_obs call (line 701).

parse_building_parts() lifted verbatim from the script (line 512).
DO NOT alter the regex without auditing the reference script.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.source_parsing.page_map import find_first, parse_decimal
from app.services.source_parsing.types import ObservationDraft

_SECTION = "building_parts"
_NS = "building_parts"


def parse_building_parts(text: str) -> list[dict[str, Any]]:
    """Parse building-parts table from the full EHR PDF text.

    Lifted verbatim from parse_building_parts() in the script (line 512).
    Returns a list of part dicts: {part_identifier, part_type, shape_no,
    part_name, part_use, part_area_m2, source}.
    """
    m = re.search(r"Ehitise osad\s+Osa nr Näitaja EHR andmed\s+(.+?)\s+Kokku\s+", text, re.S)
    if not m:
        return []

    block = re.sub(r"---PAGE---.*?Osa nr Näitaja EHR andmed\s+", " ", m.group(1), flags=re.S)
    segments = re.split(r"(?=Ehitise osa tüüp)", block)

    parts: list[dict[str, Any]] = []
    idx = 1
    for seg in segments[1:]:
        seg = seg.strip()
        if not seg:
            continue
        part_type = find_first(r"^Ehitise osa tüüp\s+(.+?)\s+Sissepääsu korrus", seg, re.S)
        shape_no = find_first(r"Ehitise kuju, kus hooneosa\s+asub\s+(\d+)", seg, re.S)
        part_name = find_first(r"Ehitise osa nimetus\s*(.*?)\s+Kasutamise otstarve", seg, re.S)
        part_use = find_first(r"Kasutamise otstarve\s+(.+?)\s+Hooneosa aadress", seg, re.S)
        part_area = find_first(r"Ehitise osa pind \(m2\)\s+([0-9 ]+,\d+)", seg, re.S)
        if not any([part_type, part_name, part_use, part_area]):
            continue
        parts.append({
            "part_identifier": f"part_{idx}",
            "part_type": part_type,
            "shape_no": int(shape_no) if shape_no and shape_no.isdigit() else None,
            "part_name": part_name or None,
            "part_use": part_use,
            "part_area_m2": parse_decimal(part_area),
            "source": "pdf",
        })
        idx += 1

    return parts


def extract_building_parts(text: str) -> list[ObservationDraft]:
    """Extract building_parts-namespace observations from the full EHR PDF text.

    Inputs:
      text — full document text (pages joined with '---PAGE---').
    Outputs:
      list[ObservationDraft] — one observation with the entire parts list,
      or empty list if no parts block found.
    """
    parts = parse_building_parts(text)
    if not parts:
        return []

    # Page hardcoded to 4 per reference script's add_obs call (line 701)
    # TODO(2.4 review): page is hardcoded to 4; EHR PDFs consistently place this on page 4
    return [
        ObservationDraft(
            namespace=_NS,
            key="building_parts",
            section=_SECTION,
            value=parts,
            unit=None,
            evidence_text="Ehitise osad",
            page_number=4,
        )
    ]
