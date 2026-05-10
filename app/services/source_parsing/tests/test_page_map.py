"""Synthetic-text unit tests for build_page_map, find_with_page, find_first.

All tests use constructed strings — no PDF required.
"""

from __future__ import annotations

import re

import pytest

from app.services.source_parsing.page_map import (
    build_page_map,
    find_first,
    find_with_page,
    normalize_multiline_value,
    parse_decimal,
)


# ---------------------------------------------------------------------------
# normalize_multiline_value
# ---------------------------------------------------------------------------


def test_normalize_collapses_newlines() -> None:
    assert normalize_multiline_value("foo\n  bar") == "foo bar"


def test_normalize_removes_non_breaking_space() -> None:
    assert normalize_multiline_value("foo bar") == "foo bar"


def test_normalize_none_returns_none() -> None:
    assert normalize_multiline_value(None) is None


def test_normalize_empty_string_returns_none() -> None:
    assert normalize_multiline_value("   ") is None


# ---------------------------------------------------------------------------
# parse_decimal
# ---------------------------------------------------------------------------


def test_parse_decimal_comma_separator() -> None:
    assert parse_decimal("1 648,00") == pytest.approx(1648.0)


def test_parse_decimal_no_thousands() -> None:
    assert parse_decimal("12,5") == pytest.approx(12.5)


def test_parse_decimal_none_returns_none() -> None:
    assert parse_decimal(None) is None


def test_parse_decimal_non_numeric_returns_none() -> None:
    assert parse_decimal("not-a-number") is None


# ---------------------------------------------------------------------------
# build_page_map
# ---------------------------------------------------------------------------


def test_build_page_map_splits_on_sentinel() -> None:
    text = "page one\n---PAGE---\npage two\n---PAGE---\npage three"
    pm = build_page_map(text)
    assert len(pm) == 3
    # split() preserves surrounding newlines verbatim; use strip() for content checks
    assert pm[1].strip() == "page one"
    assert pm[2].strip() == "page two"
    assert pm[3].strip() == "page three"


def test_build_page_map_no_sentinel_returns_page_1() -> None:
    pm = build_page_map("no separator here")
    assert pm == {1: "no separator here"}


# ---------------------------------------------------------------------------
# find_with_page
# ---------------------------------------------------------------------------


def test_find_with_page_returns_match_on_correct_page() -> None:
    pm = {
        1: "irrelevant content",
        2: "Ehitisregistri kood 101035685 more text",
        3: "other page",
    }
    value, page, evidence = find_with_page(r"Ehitisregistri kood\s+(\d+)", pm)
    assert value == "101035685"
    assert page == 2
    assert evidence is not None
    assert "101035685" in (evidence or "")


def test_find_with_page_returns_none_when_not_found() -> None:
    pm = {1: "nothing here"}
    value, page, evidence = find_with_page(r"Ehitisregistri kood\s+(\d+)", pm)
    assert value is None
    assert page is None
    assert evidence is None


def test_find_with_page_scans_pages_in_order() -> None:
    pm = {
        1: "Näitaja first 100",
        2: "Näitaja second 200",
    }
    value, page, _ = find_with_page(r"Näitaja\s+\w+\s+(\d+)", pm)
    # Should return match from page 1 (lower page number comes first)
    assert page == 1
    assert value == "100"


def test_find_with_page_multiline_flag() -> None:
    pm = {
        1: "Ehitise aadress\nLai tn 1\nEhitisregistri kood",
    }
    value, page, _ = find_with_page(
        r"Ehitise aadress\s+(.+?)\s+Ehitisregistri kood", pm, re.S
    )
    assert value == "Lai tn 1"
    assert page == 1


# ---------------------------------------------------------------------------
# find_first
# ---------------------------------------------------------------------------


def test_find_first_returns_group1() -> None:
    text = "Ehitise osa tüüp Eluruum Sissepääsu korrus 1"
    result = find_first(r"Ehitise osa tüüp\s+(.+?)\s+Sissepääsu korrus", text, re.S)
    assert result == "Eluruum"


def test_find_first_returns_none_when_no_match() -> None:
    assert find_first(r"NoMatch\s+(\d+)", "no match here") is None
