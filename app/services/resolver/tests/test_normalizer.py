"""Tests for app/services/resolver/normalizer.py."""

from app.services.resolver.normalizer import normalize_address


def test_raw_is_preserved() -> None:
    result = normalize_address("Lai tn 1, Tallinn")
    assert result.raw == "Lai tn 1, Tallinn"


def test_lowercase() -> None:
    result = normalize_address("LAI TN 1")
    assert result.normalized == "lai tn 1"


def test_estonian_chars_replaced() -> None:
    result = normalize_address("Jõe tn, Pärnu")
    # õ→o, ä→a
    assert "jo" in result.normalized
    assert "parn" in result.normalized


def test_all_estonian_chars() -> None:
    result = normalize_address("äöüõ")
    assert result.normalized == "aouo"


def test_non_alphanumeric_collapsed_to_space() -> None:
    result = normalize_address("Lai, tn. 1 // Nunne")
    assert "//" not in result.normalized
    assert "  " not in result.normalized


def test_leading_trailing_spaces_stripped() -> None:
    result = normalize_address("  Lai tn 1  ")
    assert result.normalized == "lai tn 1"


def test_empty_string() -> None:
    result = normalize_address("")
    assert result.raw == ""
    assert result.normalized == ""


def test_only_special_chars() -> None:
    result = normalize_address("///---")
    assert result.normalized == ""


def test_house_number_preserved() -> None:
    result = normalize_address("Pelguranna tn 14a")
    assert "14a" in result.normalized


def test_postcode_preserved() -> None:
    result = normalize_address("Lai 1, 10133 Tallinn")
    assert "10133" in result.normalized
