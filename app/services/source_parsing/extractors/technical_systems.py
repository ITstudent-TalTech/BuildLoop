"""Technical systems namespace extractor.

Produces observations for:
  technical_systems.electricity
  technical_systems.water
  technical_systems.sewer
  technical_systems.heat_source
  technical_systems.gas
  technical_systems.ventilation
  technical_systems.lift_count

Regex patterns lifted verbatim from field_specs in parse_pdf_to_passport()
(buildloop_passport_from_address.py lines 588-594).
DO NOT alter patterns without auditing the reference script.
"""

from __future__ import annotations

import re

from app.services.source_parsing.page_map import find_with_page
from app.services.source_parsing.types import ObservationDraft

_SECTION = "technical_systems"
_NS = "technical_systems"

# (key, pattern, value_type)
# lift_count is an integer; all others are strings
_FIELD_SPECS: list[tuple[str, str, str]] = [
    ("electricity", r"Elektrisüsteemi liik\s+(.+?)\s+Veevarustuse liik",     "str"),
    ("water",       r"Veevarustuse liik\s+(.+?)\s+Kanalistasiooni liik",     "str"),
    ("sewer",       r"Kanalistasiooni liik\s+(.+?)\s+Soojusallika liik",     "str"),
    ("heat_source", r"Soojusallika liik\s+(.+?)\s+Energiaallika liik",       "str"),
    ("gas",         r"Energiaallika liik\s+(.+?)\s+Ventilatsiooni liik",     "str"),
    ("ventilation", r"Ventilatsiooni liik\s+(.+?)\s+Jahutussüsteemi liik",  "str"),
    ("lift_count",  r"Liftide arv\s+(\d+)",                                  "int"),
]


def extract_technical_systems(page_map: dict[int, str]) -> list[ObservationDraft]:
    """Extract technical_systems-namespace observations from an EHR PDF page map.

    Inputs:
      page_map — {page_number: page_text} from build_page_map().
    Outputs:
      list[ObservationDraft] for all found technical system fields.
    """
    drafts: list[ObservationDraft] = []

    for key, pattern, vtype in _FIELD_SPECS:
        raw_value, page, evidence = find_with_page(pattern, page_map, re.S)
        if raw_value is None:
            continue

        value: object = int(float(raw_value)) if vtype == "int" else raw_value

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
