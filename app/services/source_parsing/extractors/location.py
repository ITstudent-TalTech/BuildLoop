"""Location namespace extractor.

Produces observations for:
  location.geometry_method
  location.shape_type
  location.coordinates

parse_geometry() lifted verbatim from buildloop_passport_from_address.py
(line 489). DO NOT alter the regex without auditing the reference script.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.source_parsing.page_map import find_with_page, normalize_multiline_value
from app.services.source_parsing.types import ObservationDraft

_SECTION = "location"
_NS = "location"


def parse_geometry(page_map: dict[int, str]) -> dict[str, Any]:
    """Parse geometry block from the EHR PDF.

    Lifted verbatim from parse_geometry() in the script (line 489).
    Returns dict with geometry_method, shape_type, coordinates, page.
    """
    value, page, _ = find_with_page(
        r"Ehitise asukoht\s+Kuju nr Näitaja EHR andmed\s+1 Nimetus\s+"
        r"Geomeetria moodustusviis\s+(.+?)\s+Ehitisel on",
        page_map, re.S
    )
    if value is None:
        return {"geometry_method": None, "shape_type": None, "coordinates": [], "page": None}

    method_match = re.search(r"^(.+?)\s+Tüüp", value, re.S)
    shape_type_match = re.search(r"Tüüp\s+(.+?)\s+Koordinaadid", value, re.S)
    coords_block_match = re.search(r"Koordinaadid\s+(.+?)\s+Kuju aadressid", value, re.S)

    coords: list[dict[str, float]] = []
    if coords_block_match:
        pairs = re.findall(r"([0-9]+\.[0-9]+)\s+([0-9]+\.[0-9]+)", coords_block_match.group(1))
        for y, x in pairs:
            coords.append({"y": float(y), "x": float(x)})

    return {
        "geometry_method": normalize_multiline_value(method_match.group(1)) if method_match else None,
        "shape_type": normalize_multiline_value(shape_type_match.group(1)) if shape_type_match else None,
        "coordinates": coords,
        "page": page,
    }


def extract_location(page_map: dict[int, str]) -> list[ObservationDraft]:
    """Extract location-namespace observations from an EHR PDF page map.

    Inputs:
      page_map — {page_number: page_text} from build_page_map().
    Outputs:
      list[ObservationDraft] for geometry_method, shape_type, and/or coordinates.
    """
    geo = parse_geometry(page_map)
    page = geo["page"]
    drafts: list[ObservationDraft] = []

    if geo["geometry_method"] is not None:
        drafts.append(ObservationDraft(
            namespace=_NS,
            key="geometry_method",
            section=_SECTION,
            value=geo["geometry_method"],
            evidence_text="Ehitise asukoht / Geomeetria moodustusviis",
            page_number=page,
        ))

    if geo["shape_type"] is not None:
        drafts.append(ObservationDraft(
            namespace=_NS,
            key="shape_type",
            section=_SECTION,
            value=geo["shape_type"],
            evidence_text="Ehitise asukoht / Tüüp",
            page_number=page,
        ))

    if geo["coordinates"]:
        drafts.append(ObservationDraft(
            namespace=_NS,
            key="coordinates",
            section=_SECTION,
            value=geo["coordinates"],
            evidence_text="Ehitise asukoht / Koordinaadid",
            page_number=page,
        ))

    return drafts
