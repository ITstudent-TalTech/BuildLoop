"""Internal type definitions for the resolver service.

These types are NOT the API layer — they are service-internal.
Pydantic API response shapes live in app/schemas/resolution.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


@dataclass
class NormalizedAddress:
    """A user-supplied address in two forms: original and token-match-ready."""

    raw: str
    """Original string exactly as supplied by the user."""

    normalized: str
    """Lowercased, diacritics-removed, non-alphanumeric-stripped form used
    for token overlap and number matching."""


@dataclass
class QueryVariant:
    """One query string to send to In-ADS, tagged with its generation strategy."""

    query: str
    tag: str
    """One of: "exact", "no_apt", "alternate_street_form"."""


@dataclass
class InAdsResponse:
    """Result of one In-ADS gazetteer HTTP call."""

    ok: bool
    data: Any
    """Parsed JSON body (dict or list), or None on error."""

    ssl_fallback_used: bool = False
    error: str | None = None
    status_code: int | None = None


@dataclass
class CandidateGroup:
    """All In-ADS hits for a single EHR code, with aliases merged in.

    Corner addresses (doc 03 Rule 2): if the same EHR code appears under
    multiple official addresses (e.g. "Lai tn 1 // Nunne tn 4"), all
    address strings are collected in address_aliases rather than treated
    as competing buildings.
    """

    ehr_code: str
    normalized_address: str | None
    """Primary address from In-ADS (taisaadress, full canonical form)."""

    address_aliases: list[str]
    """All address strings for this EHR code, including the primary one."""

    raw_hits: list[dict[str, Any]]
    """Raw bag entries from walk_for_ehr_candidates — preserved for audit."""

    object_types: list[str]
    matched_variants: list[QueryVariant] = field(default_factory=list)
    """Which query variants produced a hit for this EHR code."""

    in_ads_primary: bool = False
    """True when In-ADS marked this address entry with primary='true' (canonical match signal)."""


@dataclass
class ScoredCandidate:
    """A CandidateGroup after confidence scoring."""

    ehr_code: str
    normalized_address: str | None
    address_aliases: list[str]
    confidence_score: float
    match_reasons: list[str]
    object_types: list[str]
    matched_variants: list[QueryVariant]
    raw_candidate: dict[str, Any] | None


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


@dataclass
class ResolverThresholds:
    """Score thresholds that control auto-resolve vs. ambiguous vs. unresolved."""

    auto_resolve: float = 0.85
    ambiguous: float = 0.50


@dataclass
class ResolutionResult:
    """The final result returned by ResolverService to the API layer."""

    status: ResolutionStatus
    resolution_run_id: UUID
    ehr_code: str | None = None
    normalized_address: str | None = None
    address_aliases: list[str] = field(default_factory=list)
    confidence_score: float | None = None
    candidates: list[ScoredCandidate] = field(default_factory=list)
    reason: str | None = None
