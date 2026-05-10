"""Building profile namespace extractor.

Produces observations for:
  building_profile.building_type
  building_profile.building_status
  building_profile.building_name
  building_profile.use_categories
  building_profile.floors.above_ground
  building_profile.floors.below_ground
  building_profile.footprint_area_m2
  building_profile.heated_area_m2
  building_profile.net_area_m2
  building_profile.public_use_area_m2
  building_profile.technical_area_m2
  building_profile.height_m
  building_profile.length_m
  building_profile.width_m
  building_profile.depth_m
  building_profile.volume_m3

Regex patterns lifted verbatim from field_specs in parse_pdf_to_passport()
(buildloop_passport_from_address.py lines 566-580) and parse_use_categories()
(line 468). DO NOT alter patterns without auditing the reference script.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.source_parsing.page_map import (
    find_with_page,
    normalize_multiline_value,
    parse_decimal,
)
from app.services.source_parsing.types import ObservationDraft

_SECTION = "building_profile"
_NS = "building_profile"


def parse_use_categories(text: str) -> list[dict[str, Any]]:
    """Parse the use-categories table from the full EHR PDF text.

    Lifted verbatim from parse_use_categories() in the script (line 468).
    Returns a list of {name, classifier_code, area_m2, source} dicts.
    """
    m = re.search(
        r"Ehitise kasutamise otstarbed\s+Näitaja EHR andmed\s+Kasutamise otstarve,"
        r"\s+mitteeluruumi pind \(m2\)\s+(.+?)\s+Eluruumide pind kokku",
        text, re.S
    )
    if not m:
        return []
    block = normalize_multiline_value(m.group(1)) or ""
    matches = re.findall(r"([^,]+?\(\d+\))\s*,?\s*([0-9 ]+,\d+)", block)
    out: list[dict[str, Any]] = []
    for raw_name, raw_area in matches:
        code_match = re.search(r"\((\d+)\)", raw_name)
        out.append({
            "name": re.sub(r"\s*\(\d+\)\s*$", "", normalize_multiline_value(raw_name) or "").strip(),
            "classifier_code": code_match.group(1) if code_match else None,
            "area_m2": parse_decimal(raw_area),
            "source": "pdf",
        })
    return out


# (pattern, unit, value_type)
# value_type: "str" | "float" | "int"
_FIELD_SPECS: list[tuple[str, str, str | None, str]] = [
    ("building_type",        r"Ehitise liik\s+(.+?)\s+Ehitise seisund",                       None,  "str"),
    ("building_status",      r"Ehitise seisund\s+(.+?)\s+Ehitise nimetus",                     None,  "str"),
    ("building_name",        r"Ehitise nimetus\s+(.+?)\s+Omandi liik",                         None,  "str"),
    ("footprint_area_m2",    r"Ehitisealune pind \(m2\)\s+([0-9 ]+,\d+)",                      "m2",  "float"),
    ("heated_area_m2",       r"Köetav pind \(m2\)\s+([0-9 ]+,\d+)",                            "m2",  "float"),
    ("net_area_m2",          r"Suletud netopind \(m2\)\s+([0-9 ]+,\d+)",                       "m2",  "float"),
    ("public_use_area_m2",   r"Üldkasutatav pind \(m2\)\s+([0-9 ]+,\d+)",                     "m2",  "float"),
    ("technical_area_m2",    r"Tehnopind \(m2\)\s+([0-9 ]+,\d+)",                             "m2",  "float"),
    ("floors.above_ground",  r"Maapealsete korruste arv\s+(\d+)",                               None,  "int"),
    ("floors.below_ground",  r"Maa-aluste korruste arv\s+(\d+)",                               None,  "int"),
    ("height_m",             r"Kõrgus \(m\)\s+([0-9 ]+,\d+)",                                 "m",   "float"),
    ("length_m",             r"Pikkus \(m\)\s+([0-9 ]+,\d+)",                                 "m",   "float"),
    ("width_m",              r"Laius \(m\)\s+([0-9 ]+,\d+)",                                  "m",   "float"),
    ("depth_m",              r"Sügavus \(m\)\s+([0-9 ]+,\d+)",                                "m",   "float"),
    ("volume_m3",            r"Maht \(m3\)\s+([0-9 ]+,\d+)",                                  "m3",  "float"),
]


def extract_building_profile(page_map: dict[int, str]) -> list[ObservationDraft]:
    """Extract building_profile-namespace observations from an EHR PDF page map.

    Inputs:
      page_map — {page_number: page_text} from build_page_map().
    Outputs:
      list[ObservationDraft] for all found building_profile fields.
    """
    # Build full text for use_categories (needs cross-page search)
    full_text = "\n---PAGE---\n".join(page_map[p] for p in sorted(page_map))

    drafts: list[ObservationDraft] = []

    for key, pattern, unit, vtype in _FIELD_SPECS:
        raw_value, page, evidence = find_with_page(pattern, page_map, re.S)
        if raw_value is None:
            continue

        if vtype == "float":
            value: object = parse_decimal(raw_value)
        elif vtype == "int":
            value = int(float(raw_value))
        else:
            value = raw_value

        if value is None:
            continue

        drafts.append(ObservationDraft(
            namespace=_NS,
            key=key,
            section=_SECTION,
            value=value,
            unit=unit,
            evidence_text=(evidence or "")[:1200] or None,
            page_number=page,
        ))

    # use_categories — parsed separately; page hardcoded to 1 per the script
    # TODO(2.4 review): page is hardcoded to 1; EHR PDFs consistently place this on page 1
    use_categories = parse_use_categories(full_text)
    if use_categories:
        drafts.append(ObservationDraft(
            namespace=_NS,
            key="use_categories",
            section=_SECTION,
            value=use_categories,
            unit=None,
            evidence_text="Ehitise kasutamise otstarbed",
            page_number=1,
        ))

    return drafts
