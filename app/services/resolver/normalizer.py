"""Address normalization for token-based matching.

Lifted from normalize_address_for_match() in buildloop_passport_from_address.py
(line 166). Restructured to return a NormalizedAddress dataclass that carries
both the raw original and the match-ready normalized form.
"""

from __future__ import annotations

import re

from app.services.resolver.types import NormalizedAddress


def normalize_address(raw: str) -> NormalizedAddress:
    """Normalize a raw address string for fuzzy token matching.

    Inputs:  raw address string as supplied by the user.
    Outputs: NormalizedAddress with the original raw form preserved and a
             lowercased, diacritic-stripped, non-alphanumeric-collapsed
             normalized form ready for token overlap comparisons.

    Character replacements match the script exactly (ä→a, ö→o, ü→u, õ→o).
    Non-alphanumeric runs become single spaces; leading/trailing space stripped.
    """
    normalized = raw.lower()
    normalized = (
        normalized
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("õ", "o")
    )
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return NormalizedAddress(raw=raw, normalized=normalized)
