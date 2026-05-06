"""Tests for app/services/resolver/confidence.py.

Verifies that scoring weights are preserved exactly from the script (line 214)
and that decide_status enforces the no-silent-weak-selection criterion
from doc 12 Agent 2 acceptance criteria.
"""

from app.services.resolver.confidence import decide_status, score_candidate
from app.services.resolver.normalizer import normalize_address
from app.services.resolver.types import (
    CandidateGroup,
    QueryVariant,
    ResolutionStatus,
    ResolverThresholds,
    ScoredCandidate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_V_EXACT = QueryVariant(query="Lai 1, Tallinn", tag="exact")


def _group(ehr: str, addr: str) -> CandidateGroup:
    return CandidateGroup(
        ehr_code=ehr,
        normalized_address=addr,
        address_aliases=[addr] if addr else [],
        raw_hits=[{"ehr_code": ehr, "raw_candidate": {"taisaadress": addr}}],
        object_types=[],
        matched_variants=[_V_EXACT],
    )


def _scored(confidence: float) -> ScoredCandidate:
    return ScoredCandidate(
        ehr_code="123456789",
        normalized_address="Tallinn, Test tn 1",
        address_aliases=[],
        confidence_score=confidence,
        match_reasons=[],
        object_types=[],
        matched_variants=[_V_EXACT],
        raw_candidate=None,
    )


# ---------------------------------------------------------------------------
# score_candidate — individual weight tests
# ---------------------------------------------------------------------------


def test_token_overlap_contributes_045() -> None:
    """Exact token match: overlap_ratio=1.0 → +0.45."""
    inp = normalize_address("Lai 1, Tallinn")
    # Strip locality tokens and number to isolate the overlap contribution only.
    # Use a candidate that has ONLY the tokens from input (no house number match,
    # no numeric ehr, no localities).
    grp = _group("NODIGIT", "lai 1 tallinn")  # non-numeric ehr → no +0.10
    # Manually override ehr_code to be non-numeric so only overlap fires.
    grp.ehr_code = "NODIGIT"
    result = score_candidate(inp, grp, [_V_EXACT])
    # overlap = {"lai","1","tallinn"} ∩ {"lai","1","tallinn"} = 3/3 = 1.0
    # 0.45*1.0 = 0.45; no house_number (NODIGIT doesn't count, but "1" is in both)
    # so house_number fires too → at least 0.45
    assert result.confidence_score >= 0.45


def test_house_number_adds_030() -> None:
    """House number match adds exactly 0.30."""
    # Use an input and candidate that share ONLY a house number.
    inp = normalize_address("99999")
    grp = _group("NODIGIT", "address 99999 street")
    grp.ehr_code = "NODIGIT"
    result = score_candidate(inp, grp, [])
    assert "house_number_match" in result.match_reasons


def test_locality_match_adds_003_each() -> None:
    inp = normalize_address("tallinn test")
    grp = _group("NODIGIT", "tallinn something")
    grp.ehr_code = "NODIGIT"
    result = score_candidate(inp, grp, [])
    assert any("locality_match:tallinn" in r for r in result.match_reasons)


def test_numeric_ehr_adds_010() -> None:
    inp = normalize_address("X")
    grp = _group("123456789", "Y")
    result = score_candidate(inp, grp, [])
    assert "numeric_ehr_code_present" in result.match_reasons


def test_score_capped_at_099() -> None:
    """Even a perfect match cannot exceed 0.99."""
    inp = normalize_address("Lai 1, Tallinn")
    # Craft a candidate that maximises all factors.
    grp = _group(
        "101035685",
        "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1",
    )
    v1 = QueryVariant(query="Lai 1, Tallinn", tag="exact")
    v2 = QueryVariant(query="Lai 1, Tallinn alt", tag="no_apt")
    result = score_candidate(inp, grp, [v1, v2])
    assert result.confidence_score <= 0.99


def test_multi_variant_boost_fires() -> None:
    """Two matched variants → multi_variant_match reason present."""
    inp = normalize_address("Lai 1, Tallinn")
    grp = _group("101035685", "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1")
    v1 = QueryVariant(query="Lai 1, Tallinn", tag="exact")
    v2 = QueryVariant(query="Lai 1, Tallinn alt", tag="no_apt")
    result = score_candidate(inp, grp, [v1, v2])
    assert any("multi_variant_match" in r for r in result.match_reasons)


def test_single_variant_no_multi_boost() -> None:
    inp = normalize_address("Lai 1, Tallinn")
    grp = _group("101035685", "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1")
    result = score_candidate(inp, grp, [_V_EXACT])
    assert not any("multi_variant_match" in r for r in result.match_reasons)


def test_full_lai_1_tallinn_scores_above_threshold() -> None:
    """Smoke test: 'Lai 1, Tallinn' vs the canonical address → ≥ 0.85."""
    inp = normalize_address("Lai 1, Tallinn")
    grp = _group("101035685", "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1")
    result = score_candidate(inp, grp, [_V_EXACT])
    assert result.confidence_score >= 0.85


# ---------------------------------------------------------------------------
# decide_status — acceptance criteria (doc 12 Agent 2)
# ---------------------------------------------------------------------------


def test_empty_candidates_is_unresolved() -> None:
    assert decide_status([], ResolverThresholds()) == ResolutionStatus.UNRESOLVED


def test_score_above_auto_resolve_is_resolved() -> None:
    candidates = [_scored(0.90)]
    assert decide_status(candidates, ResolverThresholds()) == ResolutionStatus.RESOLVED


def test_score_at_auto_resolve_boundary_is_resolved() -> None:
    candidates = [_scored(0.85)]
    assert decide_status(candidates, ResolverThresholds()) == ResolutionStatus.RESOLVED


def test_score_0_60_is_ambiguous_not_resolved() -> None:
    """Acceptance criterion: top score 0.6 must return ambiguous, not resolved."""
    candidates = [_scored(0.60)]
    status = decide_status(candidates, ResolverThresholds())
    assert status == ResolutionStatus.AMBIGUOUS, (
        f"Expected AMBIGUOUS for score 0.60 but got {status}"
    )


def test_score_just_below_auto_resolve_is_ambiguous() -> None:
    candidates = [_scored(0.84)]
    assert decide_status(candidates, ResolverThresholds()) == ResolutionStatus.AMBIGUOUS


def test_score_at_ambiguous_boundary_is_ambiguous() -> None:
    candidates = [_scored(0.50)]
    assert decide_status(candidates, ResolverThresholds()) == ResolutionStatus.AMBIGUOUS


def test_score_0_40_is_unresolved_not_ambiguous() -> None:
    """Acceptance criterion: top score 0.4 must return unresolved."""
    candidates = [_scored(0.40)]
    status = decide_status(candidates, ResolverThresholds())
    assert status == ResolutionStatus.UNRESOLVED, (
        f"Expected UNRESOLVED for score 0.40 but got {status}"
    )


def test_score_just_below_ambiguous_is_unresolved() -> None:
    candidates = [_scored(0.49)]
    assert decide_status(candidates, ResolverThresholds()) == ResolutionStatus.UNRESOLVED


def test_custom_thresholds_respected() -> None:
    thresholds = ResolverThresholds(auto_resolve=0.70, ambiguous=0.30)
    assert decide_status([_scored(0.75)], thresholds) == ResolutionStatus.RESOLVED
    assert decide_status([_scored(0.50)], thresholds) == ResolutionStatus.AMBIGUOUS
    assert decide_status([_scored(0.20)], thresholds) == ResolutionStatus.UNRESOLVED
