"""Structural systems namespace extractor.

Produces observations for:
  structural_systems.foundation_type
  structural_systems.load_bearing_material
  structural_systems.wall_type
  structural_systems.facade_finish_material
  structural_systems.floor_structure_material
  structural_systems.roof_structure_material
  structural_systems.roof_covering_material

Regex patterns lifted verbatim from field_specs in parse_pdf_to_passport()
(buildloop_passport_from_address.py lines 581-587).
DO NOT alter patterns without auditing the reference script.
"""

from __future__ import annotations

import re

from app.services.source_parsing.page_map import find_with_page
from app.services.source_parsing.types import ObservationDraft

_SECTION = "structural_systems"
_NS = "structural_systems"

_FIELD_SPECS: list[tuple[str, str]] = [
    ("foundation_type",          r"Vundamendi liik\s+(.+?)\s+Kande- ja jäigastavate"),
    ("load_bearing_material",    r"Kande- ja jäigastavate\s+konstruktsioonide materjali liik\s+(.+?)\s+Välisseina liik"),
    ("wall_type",                r"Välisseina liik\s+(.+?)\s+Välisseina välisviimistluse"),
    ("facade_finish_material",   r"Välisseina välisviimistluse\s+materjali liik\s+(.+?)\s+Vahelagede kandva osa"),
    ("floor_structure_material", r"Vahelagede kandva osa\s+materjali liik\s+(.+?)\s+Katuse ja katuslagede kandva"),
    ("roof_structure_material",  r"Katuse ja katuslagede kandva\s+osa materjali liik\s+(.+?)\s+Katusekatte materjali liik"),
    ("roof_covering_material",   r"Katusekatte materjali liik\s+(.+?)\s+Ehitise tehnilised näitajad"),
]


def extract_structural_systems(page_map: dict[int, str]) -> list[ObservationDraft]:
    """Extract structural_systems-namespace observations from an EHR PDF page map.

    Inputs:
      page_map — {page_number: page_text} from build_page_map().
    Outputs:
      list[ObservationDraft] for all found structural system fields.
    """
    drafts: list[ObservationDraft] = []

    for key, pattern in _FIELD_SPECS:
        value, page, evidence = find_with_page(pattern, page_map, re.S)
        if value is None:
            continue
        drafts.append(ObservationDraft(
            namespace=_NS,
            key=key,
            section=_SECTION,
            value=value,
            unit=None,
            evidence_text=(evidence or "")[:1200] or None,
            page_number=page,
        ))

    return drafts
