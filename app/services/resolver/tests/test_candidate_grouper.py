"""Tests for app/services/resolver/candidate_grouper.py."""

import json
from pathlib import Path
from typing import Any

from app.services.resolver.candidate_grouper import (
    _extract_corner_aliases,
    _walk_for_ehr_candidates,
    group_candidates,
    merge_variant_groups,
)
from app.services.resolver.types import QueryVariant

FIXTURES = Path(__file__).parent / "fixtures" / "inads_responses"


def _fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# _walk_for_ehr_candidates
# ---------------------------------------------------------------------------


def test_walk_direct_ehr_kood() -> None:
    data = {"ehr_kood": "101035685", "taisaadress": "Tallinn, Lai tn 1"}
    bag: list[Any] = []
    _walk_for_ehr_candidates(data, bag)
    codes = [b["ehr_code"] for b in bag]
    assert "101035685" in codes


def test_walk_ehr_list() -> None:
    data = {
        "addresses": [
            {
                "taisaadress": "Tallinn, Lai tn 1",
                "ehr": [{"ehr_kood": "101035685"}],
            }
        ]
    }
    bag: list[Any] = []
    _walk_for_ehr_candidates(data, bag)
    codes = [b["ehr_code"] for b in bag]
    assert "101035685" in codes


def test_walk_nested_list() -> None:
    data = [{"ehr_kood": "100000001"}, {"ehr_kood": "100000002"}]
    bag: list[Any] = []
    _walk_for_ehr_candidates(data, bag)
    codes = [b["ehr_code"] for b in bag]
    assert "100000001" in codes
    assert "100000002" in codes


def test_walk_ignores_non_dict_list_items() -> None:
    data = {"ehr_kood": "abc", "other": [1, 2, 3]}
    bag: list[Any] = []
    _walk_for_ehr_candidates(data, bag)
    # "abc" is not a str/int matching the condition (it is a str, so it IS added)
    # but it is non-numeric and filtered in group_candidates
    assert all(isinstance(b["ehr_code"], str) for b in bag)


# ---------------------------------------------------------------------------
# group_candidates
# ---------------------------------------------------------------------------


def test_group_single_match() -> None:
    raw = _fixture("lai_1_resolved.json")
    bag: list[Any] = []
    _walk_for_ehr_candidates(raw, bag)
    groups = group_candidates(bag)
    codes = {g.ehr_code for g in groups}
    assert "101035685" in codes


def test_group_filters_non_numeric_ehr() -> None:
    bag = [
        {"ehr_code": "NOTANUMBER", "raw_candidate": {"taisaadress": "X"}},
        {"ehr_code": "123456789", "raw_candidate": {"taisaadress": "Y"}},
    ]
    groups = group_candidates(bag)
    codes = {g.ehr_code for g in groups}
    assert "NOTANUMBER" not in codes
    assert "123456789" in codes


def test_corner_address_aliases_from_slash() -> None:
    """A single entry with // in taisaadress should produce address_aliases."""
    raw = _fixture("lai_1_corner.json")
    bag: list[Any] = []
    _walk_for_ehr_candidates(raw, bag)
    groups = group_candidates(bag)
    assert len(groups) == 1
    grp = groups[0]
    assert grp.ehr_code == "101035685"
    assert "//" in (grp.normalized_address or "")
    assert "Lai tn 1" in grp.address_aliases
    assert "Nunne tn 4" in grp.address_aliases


def test_two_entries_same_ehr_merged() -> None:
    """Two raw_candidates with the same EHR code become one CandidateGroup."""
    bag = [
        {"ehr_code": "101035685", "raw_candidate": {"taisaadress": "Tallinn, Lai tn 1"}},
        {"ehr_code": "101035685", "raw_candidate": {"taisaadress": "Tallinn, Nunne tn 4"}},
    ]
    groups = group_candidates(bag)
    assert len(groups) == 1
    grp = groups[0]
    assert len(grp.address_aliases) == 2


def test_variant_tag_recorded() -> None:
    bag = [{"ehr_code": "123456789", "raw_candidate": {"taisaadress": "X"}}]
    v = QueryVariant(query="X", tag="exact")
    groups = group_candidates(bag, matched_variant=v)
    assert groups[0].matched_variants == [v]


# ---------------------------------------------------------------------------
# merge_variant_groups
# ---------------------------------------------------------------------------


def test_merge_adds_new_codes() -> None:
    g1 = group_candidates(
        [{"ehr_code": "111111111", "raw_candidate": {"taisaadress": "A"}}]
    )
    g2 = group_candidates(
        [{"ehr_code": "222222222", "raw_candidate": {"taisaadress": "B"}}]
    )
    merged = merge_variant_groups(g1, g2)
    codes = {g.ehr_code for g in merged}
    assert "111111111" in codes
    assert "222222222" in codes


def test_merge_same_code_accumulates_variants() -> None:
    v1 = QueryVariant(query="A", tag="exact")
    v2 = QueryVariant(query="A alt", tag="alternate_street_form")
    g1 = group_candidates(
        [{"ehr_code": "111111111", "raw_candidate": {"taisaadress": "A"}}],
        matched_variant=v1,
    )
    g2 = group_candidates(
        [{"ehr_code": "111111111", "raw_candidate": {"taisaadress": "A"}}],
        matched_variant=v2,
    )
    merged = merge_variant_groups(g1, g2)
    assert len(merged) == 1
    tags = {v.tag for v in merged[0].matched_variants}
    assert "exact" in tags
    assert "alternate_street_form" in tags


# ---------------------------------------------------------------------------
# _extract_corner_aliases (internal helper, tested directly)
# ---------------------------------------------------------------------------


def test_extract_corner_aliases_full_address() -> None:
    addr = "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4"
    aliases = _extract_corner_aliases(addr)
    assert aliases == ["Lai tn 1", "Nunne tn 4"]


def test_extract_corner_aliases_short_form() -> None:
    aliases = _extract_corner_aliases("Lai tn 1 // Nunne tn 4")
    assert aliases == ["Lai tn 1", "Nunne tn 4"]


def test_extract_corner_aliases_non_corner() -> None:
    aliases = _extract_corner_aliases("Tallinn, Lai tn 1")
    assert aliases == []
