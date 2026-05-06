"""Query variant generation for the In-ADS address search.

The original script (resolve_address_to_ehr, line 248) queries In-ADS with
exactly one variant: the raw address as typed. This module preserves that
"exact" variant as the first (and primary) query, and adds two additional
optional variants to improve recall for edge-case inputs.

DO NOT change the order: "exact" must always be first.
"""

from __future__ import annotations

import re

from app.services.resolver.types import NormalizedAddress, QueryVariant


def generate_variants(normalized: NormalizedAddress) -> list[QueryVariant]:
    """Generate ordered query variants from a normalized address.

    Inputs:  NormalizedAddress (carries both raw and normalized forms).
    Outputs: list of QueryVariant, deduplicated, in generation order.
             "exact" is always first and always present.
             "no_apt" strips Estonian/common apartment qualifiers.
             "alternate_street_form" strips common street-type tokens.

    Only variants with distinct query strings from "exact" are added.
    """
    seen: set[str] = set()
    variants: list[QueryVariant] = []

    def _add(query: str, tag: str) -> None:
        q = re.sub(r"\s+", " ", query).strip().rstrip(",").strip()
        if q and q not in seen:
            seen.add(q)
            variants.append(QueryVariant(query=q, tag=tag))

    # Always first: exact raw address (matches the script's single query)
    _add(normalized.raw, "exact")

    # no_apt: strip apartment/unit qualifiers common in Estonian addresses
    # e.g. "Lai tn 1 korter 5, Tallinn" → "Lai tn 1, Tallinn"
    no_apt = re.sub(
        r"\b(?:korter|k)\s*\d+\b", "", normalized.raw, flags=re.IGNORECASE
    )
    no_apt = re.sub(
        r"\bapt?\.?\s*\d+\b", "", no_apt, flags=re.IGNORECASE
    )
    _add(no_apt, "no_apt")

    # alternate_street_form: drop common street-type abbreviations
    # e.g. "Lai tn 1, Tallinn" → "Lai 1, Tallinn"
    alt = re.sub(
        r"\b(?:tn|tee|pst|puiestee|mnt|maantee)\b",
        "",
        normalized.raw,
        flags=re.IGNORECASE,
    )
    _add(alt, "alternate_street_form")

    return variants
