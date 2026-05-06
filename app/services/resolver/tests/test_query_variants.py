"""Tests for app/services/resolver/query_variants.py."""

from app.services.resolver.normalizer import normalize_address
from app.services.resolver.query_variants import generate_variants


def _variants(raw: str) -> list[tuple[str, str]]:
    """Return (query, tag) tuples for the given raw address."""
    return [(v.query, v.tag) for v in generate_variants(normalize_address(raw))]


def test_exact_is_always_first() -> None:
    variants = generate_variants(normalize_address("Lai tn 1, Tallinn"))
    assert variants[0].tag == "exact"
    assert variants[0].query == "Lai tn 1, Tallinn"


def test_exact_always_present_for_non_empty_input() -> None:
    variants = generate_variants(normalize_address("Lai 1, Tallinn"))
    tags = [v.tag for v in variants]
    assert "exact" in tags


def test_no_apt_strips_korter() -> None:
    pairs = _variants("Lai tn 1 korter 5, Tallinn")
    queries = {tag: q for q, tag in pairs}
    assert "korter" not in queries.get("no_apt", "")
    assert "5" not in queries.get("no_apt", "")


def test_no_apt_strips_k_abbreviation() -> None:
    pairs = _variants("Lai tn 1 k 3, Tallinn")
    queries = {tag: q for q, tag in pairs}
    # k 3 should be stripped
    assert "k 3" not in queries.get("no_apt", "Lai tn 1 k 3, Tallinn")


def test_alternate_form_strips_tn() -> None:
    pairs = _variants("Lai tn 1, Tallinn")
    queries = {tag: q for q, tag in pairs}
    if "alternate_street_form" in queries:
        assert " tn " not in queries["alternate_street_form"]


def test_no_duplicate_queries() -> None:
    variants = generate_variants(normalize_address("Simple 1"))
    queries = [v.query for v in variants]
    assert len(queries) == len(set(queries)), "Duplicate query strings found"


def test_exact_not_duplicated_as_no_apt() -> None:
    # Address with no apartment qualifier: no_apt variant would equal exact
    variants = generate_variants(normalize_address("Lai tn 1, Tallinn"))
    tags = [v.tag for v in variants]
    # "exact" must appear exactly once
    assert tags.count("exact") == 1


def test_variants_are_non_empty_strings() -> None:
    variants = generate_variants(normalize_address("Pelguranna tn 14, Tallinn"))
    for v in variants:
        assert v.query.strip(), f"Variant {v.tag!r} has empty query"
