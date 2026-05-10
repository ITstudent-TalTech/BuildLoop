"""Identity namespace extractor.

Produces observations for:
  identity.ehr_code
  identity.normalized_address
  identity.country       (hardcoded "EE" — all MVP PDFs are Estonian)
  identity.input_address (only when address_input is provided)

Regex patterns lifted verbatim from field_specs in parse_pdf_to_passport()
(buildloop_passport_from_address.py lines 563-566).

Note: identity.address_aliases is not extracted from the PDF — aliases come
from the resolver (Building.address_aliases). The PDF does not contain
a canonical alias list.
TODO(2.4 review): if normalized_address contains '//', aliases could be
  inferred, but the reference script does not do this.
"""

from __future__ import annotations

import re

from app.services.source_parsing.page_map import find_with_page
from app.services.source_parsing.types import ObservationDraft

_SECTION = "identity"

_FIELD_SPECS: dict[str, tuple[str, str | None]] = {
    # key: (pattern, unit)
    "ehr_code": (r"Ehitisregistri kood\s+(\d+)", None),
    "normalized_address": (r"Ehitise aadress\s+(.+?)\s+Ehitisregistri kood", None),
}


def extract_identity(
    page_map: dict[int, str],
    address_input: str | None = None,
) -> list[ObservationDraft]:
    """Extract identity-namespace observations from an EHR PDF page map.

    Inputs:
      page_map      — {page_number: page_text} from build_page_map().
      address_input — the raw user-supplied address, if available.
    Outputs:
      list[ObservationDraft] — one per found field; empty list if none found.
    """
    drafts: list[ObservationDraft] = []

    for key, (pattern, unit) in _FIELD_SPECS.items():
        value, page, evidence = find_with_page(pattern, page_map, re.S)
        if value is None:
            continue
        drafts.append(ObservationDraft(
            namespace=_SECTION,
            key=key,
            section=_SECTION,
            value=value,
            unit=unit,
            evidence_text=(evidence or "")[:1200] or None,
            page_number=page,
        ))

    # country — hardcoded; EHR is the Estonian building register
    drafts.append(ObservationDraft(
        namespace=_SECTION,
        key="country",
        section=_SECTION,
        value="EE",
        evidence_text="Hardcoded: source is the Estonian EHR (Ehitisregister)",
        page_number=None,
    ))

    if address_input is not None:
        drafts.append(ObservationDraft(
            namespace=_SECTION,
            key="input_address",
            section=_SECTION,
            value=address_input,
            evidence_text="User-supplied address input",
            page_number=None,
        ))

    return drafts
