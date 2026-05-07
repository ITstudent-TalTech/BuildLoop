"""EHR candidate extraction and grouping from In-ADS JSON responses.

Logic lifted from walk_for_ehr_candidates(), extract_candidate_address(), and
the deduplication loop in resolve_address_to_ehr() (lines 173–308 of
buildloop_passport_from_address.py). Restructured to produce CandidateGroup
objects rather than flat dicts, and to merge corner-address aliases instead
of dropping duplicate EHR codes.

Corner-address aliasing (doc 03 Rule 2): when In-ADS returns multiple entries
for the same EHR code (e.g. "Lai tn 1" and "Nunne tn 4" both map to EHR
101035685), or when a single entry already contains "//" in its taisaadress,
all address strings are collected in address_aliases rather than treated as
separate buildings.

Real In-ADS response shape (hotfix after 2.2): address fields (taisaadress,
pikkaadress, etc.) live on the OUTER addresses[] entry, not on the inner ehr[]
item. The inner item carries only building metadata (ehitise_nimetus, seisund,
kasutusotstarbed, etc.). collect_raw_hits() now uses _structured_walk() as the
primary path and falls back to the generic recursive walker for non-standard
shapes.
"""

from __future__ import annotations

from typing import Any

from app.services.resolver.types import CandidateGroup, QueryVariant


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _structured_walk(data: Any) -> list[dict[str, Any]]:
    """Walk the standard In-ADS addresses[].ehr[] structure.

    For each address entry that has a non-empty ehr list, emits one raw hit per
    ehr item with address_context set to the outer address entry.  This is the
    correct path for real In-ADS responses, where address fields (taisaadress,
    pikkaadress, etc.) live on the outer node, not inside the ehr item.

    Returns an empty list if the response does not follow addresses[].ehr[] shape,
    signalling collect_raw_hits() to fall back to the generic recursive walker.
    """
    if not isinstance(data, dict):
        return []
    addresses = data.get("addresses")
    if not isinstance(addresses, list):
        return []

    bag: list[dict[str, Any]] = []
    for addr_entry in addresses:
        if not isinstance(addr_entry, dict):
            continue
        ehr_list = addr_entry.get("ehr")
        if not isinstance(ehr_list, list):
            continue
        for ehr_item in ehr_list:
            if not isinstance(ehr_item, dict):
                continue
            code = (
                ehr_item.get("ehr_kood")
                or ehr_item.get("ehrcode")
                or ehr_item.get("ehr_code")
            )
            if code:
                bag.append(
                    {
                        "ehr_code": str(code),
                        "raw_candidate": ehr_item,
                        "address_context": addr_entry,
                    }
                )
    return bag


# TODO(2.2 review): walk_for_ehr_candidates double-adds EHR candidates when the
# "ehr" list branch fires AND the recursive walk subsequently enters each ehr
# item dict and finds "ehr_kood" directly. The original script was protected
# against visible duplication by its `seen` set; here we rely on CandidateGroup
# merging. Preserving the original logic exactly per session instructions.
def _walk_for_ehr_candidates(node: Any, bag: list[dict[str, Any]]) -> None:
    """Recursively walk an In-ADS JSON tree collecting EHR code entries.

    Fallback walker for non-standard response shapes.  Appends dicts of the form
    {"ehr_code": str, "raw_candidate": dict} to bag (no address_context key).
    Lifted verbatim from walk_for_ehr_candidates() in the script (line 173).
    """
    if isinstance(node, dict):
        for k, v in node.items():
            lk = str(k).lower()
            if lk in {"ehr_kood", "ehrcode", "ehr_code"} and isinstance(v, (str, int)):
                bag.append({"ehr_code": str(v), "raw_candidate": node})
            elif lk == "ehr" and isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        for kk in ("ehr_kood", "ehrcode", "ehr_code"):
                            if kk in item and item[kk]:
                                bag.append(
                                    {"ehr_code": str(item[kk]), "raw_candidate": item}
                                )
            _walk_for_ehr_candidates(v, bag)
    elif isinstance(node, list):
        for item in node:
            _walk_for_ehr_candidates(item, bag)


def _extract_candidate_address(candidate: dict[str, Any]) -> str | None:
    """Extract the best address string from a raw candidate entry.

    Checks address_context first (outer address node in real In-ADS responses,
    where taisaadress and pikkaadress live), then falls back to raw_candidate
    (inner ehr item or direct dict from the generic recursive walker).
    Extended from extract_candidate_address() in the script (line 191).
    """
    # Real In-ADS shape: address fields on the outer address entry
    ctx = candidate.get("address_context") or {}
    if isinstance(ctx, dict):
        for key in ("taisaadress", "pikkaadress", "aadresstekst", "lahiaadress", "aadress"):
            value = ctx.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    # Fallback: inner ehr item or direct node (generic recursive walker hits)
    raw = candidate.get("raw_candidate", {})
    if not isinstance(raw, dict):
        return None

    possible_keys = [
        "taisaadress",
        "aadress",
        "address",
        "lahiaadress",
        "nimi",
        "nimetus",
        "ads_lahiaadress",
    ]
    for key in possible_keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for v in raw.values():
        if isinstance(v, dict):
            for key in possible_keys:
                value = v.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return None


def _extract_corner_aliases(normalized_address: str) -> list[str]:
    """Split a corner address into its individual street name aliases.

    "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4"
    → ["Lai tn 1", "Nunne tn 4"]

    For non-corner addresses (no "//"), returns an empty list.
    """
    if "//" not in normalized_address:
        return []
    aliases: list[str] = []
    for part in normalized_address.split("//"):
        part = part.strip()
        # Take the last comma-separated segment as the short street form.
        short = part.split(",")[-1].strip()
        if short:
            aliases.append(short)
    return aliases


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def group_candidates(
    raw_hits: list[dict[str, Any]],
    matched_variant: QueryVariant | None = None,
) -> list[CandidateGroup]:
    """Group raw In-ADS EHR entries by EHR code, merging address aliases.

    Inputs:
      raw_hits       — bag produced by _walk_for_ehr_candidates
      matched_variant — the QueryVariant that produced this hit set (for tracking)
    Outputs:
      list[CandidateGroup] — one entry per unique numeric EHR code.

    Non-numeric EHR codes are skipped (same filter as the original script).
    Corner addresses: if normalized_address contains "//" (either from a single
    In-ADS entry or from merging two entries with the same code), aliases are
    extracted via _extract_corner_aliases.
    """
    groups: dict[str, CandidateGroup] = {}

    for c in raw_hits:
        ehr_code = str(c.get("ehr_code") or "")
        if not ehr_code.isdigit():
            continue

        addr = _extract_candidate_address(c)

        if ehr_code not in groups:
            aliases: list[str] = []
            if addr:
                corner_aliases = _extract_corner_aliases(addr)
                aliases = corner_aliases if corner_aliases else [addr]

            groups[ehr_code] = CandidateGroup(
                ehr_code=ehr_code,
                normalized_address=addr,
                address_aliases=aliases,
                raw_hits=[c],
                object_types=[],
                matched_variants=[matched_variant] if matched_variant else [],
            )
        else:
            # Same EHR code: merge address aliases (corner-address handling)
            grp = groups[ehr_code]
            grp.raw_hits.append(c)
            if addr:
                corner_aliases = _extract_corner_aliases(addr)
                new_addrs = corner_aliases if corner_aliases else [addr]
                for a in new_addrs:
                    if a not in grp.address_aliases:
                        grp.address_aliases.append(a)
                # If we now have multiple aliases, rebuild normalized_address
                # as a "//" composite to signal a corner address.
                if len(grp.address_aliases) > 1 and grp.normalized_address:
                    if "//" not in grp.normalized_address:
                        grp.normalized_address = " // ".join(grp.address_aliases)
            if matched_variant and matched_variant not in grp.matched_variants:
                grp.matched_variants.append(matched_variant)

    return list(groups.values())


def collect_raw_hits(data: object) -> list[dict[str, Any]]:
    """Walk an In-ADS response and return all EHR hits.

    Primary path: _structured_walk() handles real In-ADS addresses[].ehr[]
    responses where address fields live on the outer address node.
    Fallback: generic recursive walker for non-standard response shapes.
    """
    structured = _structured_walk(data)
    if structured:
        return structured
    bag: list[dict[str, Any]] = []
    _walk_for_ehr_candidates(data, bag)
    return bag


def merge_variant_groups(
    existing: list[CandidateGroup],
    new_groups: list[CandidateGroup],
) -> list[CandidateGroup]:
    """Merge CandidateGroups from successive query variants by EHR code.

    Inputs:  existing groups (from previous variants), new groups (latest variant).
    Outputs: merged list — same EHR code across variants produces one group with
             all aliases and all matched_variants collected.
    """
    index: dict[str, CandidateGroup] = {g.ehr_code: g for g in existing}

    for ng in new_groups:
        if ng.ehr_code not in index:
            index[ng.ehr_code] = ng
        else:
            grp = index[ng.ehr_code]
            grp.raw_hits.extend(ng.raw_hits)
            for addr in ng.address_aliases:
                if addr not in grp.address_aliases:
                    grp.address_aliases.append(addr)
            for v in ng.matched_variants:
                if v not in grp.matched_variants:
                    grp.matched_variants.append(v)

    return list(index.values())
