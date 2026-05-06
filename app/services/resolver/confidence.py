"""Candidate confidence scoring and resolution status decision logic.

score_candidate() is lifted from score_candidate() in
buildloop_passport_from_address.py (line 214). The weights, bonus rules, and
threshold comparisons are preserved exactly. One additive bonus is introduced
for the multi-variant acceptance criterion (doc 12 Agent 2): a small score
boost when the same EHR code was found by more than one query variant.

decide_status() maps a sorted scored list to a ResolutionStatus using the
AUTO_RESOLVE_THRESHOLD / AMBIGUOUS_THRESHOLD values from the script (lines
58–59). The thresholds are passed in from settings, not hard-coded here.
"""

from __future__ import annotations

import re

from app.services.resolver.normalizer import normalize_address
from app.services.resolver.types import (
    CandidateGroup,
    NormalizedAddress,
    QueryVariant,
    ResolutionStatus,
    ResolverThresholds,
    ScoredCandidate,
)


def score_candidate(
    input_addr: NormalizedAddress,
    candidate: CandidateGroup,
    matched_variants: list[QueryVariant],
) -> ScoredCandidate:
    """Score one candidate against the user's input address.

    Inputs:
      input_addr      — NormalizedAddress of the user's original query.
      candidate       — CandidateGroup from In-ADS (one EHR code).
      matched_variants — QueryVariants that returned this candidate.
    Outputs:
      ScoredCandidate with confidence_score in [0, 0.99] and match_reasons list.

    Scoring weights (preserved verbatim from the script, line 214):
      token_overlap   : 0.45 × (overlap_tokens / input_tokens)  [max 0.45]
      house_number    : 0.30 if any digit token in input appears in candidate
      locality match  : 0.03 per matching token in {"tallinn","kesklinna",
                        "harju","estonia"}                       [max 0.12]
      numeric_ehr     : 0.10 if the EHR code is all digits
      multi_variant   : 0.05 if the same EHR was found by > 1 variant  [NEW]
      cap             : min(score, 0.99)
    """
    reasons: list[str] = []
    score = 0.0

    normalized_input = input_addr.normalized
    # Normalize the candidate address for token matching — uses the same
    # normalization function so the comparison is symmetric.
    normalized_candidate = normalize_address(
        candidate.normalized_address or ""
    ).normalized

    # --- token overlap (weight 0.45) ---
    input_tokens = set(normalized_input.split())
    cand_tokens = set(normalized_candidate.split())
    overlap = input_tokens & cand_tokens
    if overlap:
        overlap_ratio = len(overlap) / max(1, len(input_tokens))
        score += 0.45 * overlap_ratio
        reasons.append(f"token_overlap={overlap_ratio:.2f}")

    # --- house number match (weight 0.30) ---
    input_nums = re.findall(r"\d+[a-z]?", normalized_input)
    cand_nums = re.findall(r"\d+[a-z]?", normalized_candidate)
    if input_nums and cand_nums and any(n in cand_nums for n in input_nums):
        score += 0.30
        reasons.append("house_number_match")

    # --- locality match (weight 0.03 per token) ---
    for token in ("tallinn", "kesklinna", "harju", "estonia"):
        if token in normalized_input and token in normalized_candidate:
            score += 0.03
            reasons.append(f"locality_match:{token}")

    # --- numeric EHR code present (weight 0.10) ---
    if candidate.ehr_code.isdigit():
        score += 0.10
        reasons.append("numeric_ehr_code_present")

    # --- multi-variant bonus (additive, not in original script) ---
    # Acceptance criterion: same EHR code reached via multiple query variants
    # should boost confidence. Added here without changing existing weights.
    if len(matched_variants) > 1:
        score += 0.05
        reasons.append(f"multi_variant_match={len(matched_variants)}")

    return ScoredCandidate(
        ehr_code=candidate.ehr_code,
        normalized_address=candidate.normalized_address,
        address_aliases=candidate.address_aliases,
        confidence_score=min(score, 0.99),
        match_reasons=reasons,
        object_types=candidate.object_types,
        matched_variants=matched_variants,
        raw_candidate=candidate.raw_hits[0].get("raw_candidate") if candidate.raw_hits else None,
    )


def decide_status(
    scored: list[ScoredCandidate],
    thresholds: ResolverThresholds,
) -> ResolutionStatus:
    """Map a sorted scored candidate list to a ResolutionStatus.

    Inputs:
      scored     — list of ScoredCandidate, sorted descending by confidence_score.
      thresholds — ResolverThresholds from settings.
    Outputs:
      ResolutionStatus: RESOLVED / AMBIGUOUS / UNRESOLVED.

    Decision logic (preserved from lines 317–332 of the script):
      - empty list                              → UNRESOLVED
      - top.confidence >= auto_resolve (0.85)   → RESOLVED
      - top.confidence >= ambiguous   (0.50)    → AMBIGUOUS
      - otherwise                               → UNRESOLVED
    """
    if not scored:
        return ResolutionStatus.UNRESOLVED

    top = scored[0]
    if top.confidence_score >= thresholds.auto_resolve:
        return ResolutionStatus.RESOLVED
    if top.confidence_score >= thresholds.ambiguous:
        return ResolutionStatus.AMBIGUOUS
    return ResolutionStatus.UNRESOLVED
