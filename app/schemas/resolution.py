"""Pydantic request/response schemas for the /v1/resolutions endpoints.

All shapes match /web/lib/api/types.ts and doc 11 exactly:
  ResolutionCandidate        → ResolutionCandidate (TS)
  ResolvedResolutionResponse → ResolvedResolutionResponse (TS)
  AmbiguousResolutionResponse→ AmbiguousResolutionResponse (TS)
  UnresolvedResolutionResponse→ UnresolvedResolutionResponse (TS)
  ResolutionResponse         → ResolutionResponse (TS discriminated union)

The discriminator field is "status".
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.services.resolver.types import ResolutionResult, ResolutionStatus


# ---------------------------------------------------------------------------
# Candidate sub-model (shared by ambiguous response)
# ---------------------------------------------------------------------------


class ResolutionCandidate(BaseModel):
    """One candidate in an ambiguous resolution — matches ResolutionCandidate TS."""

    ehr_code: str
    normalized_address: str
    confidence_score: float


# ---------------------------------------------------------------------------
# Discriminated response variants
# ---------------------------------------------------------------------------


class ResolvedResolutionResponse(BaseModel):
    """Resolved response — matches ResolvedResolutionResponse TS."""

    status: Literal["resolved"] = "resolved"
    resolution_run_id: UUID
    ehr_code: str
    normalized_address: str
    address_aliases: list[str]
    confidence_score: float


class AmbiguousResolutionResponse(BaseModel):
    """Ambiguous response — matches AmbiguousResolutionResponse TS."""

    status: Literal["ambiguous"] = "ambiguous"
    resolution_run_id: UUID
    candidates: list[ResolutionCandidate]


class UnresolvedResolutionResponse(BaseModel):
    """Unresolved response — matches UnresolvedResolutionResponse TS.

    candidates is always an empty list (typed [] in TS).
    """

    status: Literal["unresolved"] = "unresolved"
    resolution_run_id: UUID
    candidates: list[Any] = Field(default_factory=list)


# Pydantic v2 discriminated union — FastAPI uses this as the response_model type.
ResolutionResponse = Annotated[
    Union[
        ResolvedResolutionResponse,
        AmbiguousResolutionResponse,
        UnresolvedResolutionResponse,
    ],
    Field(discriminator="status"),
]


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class ResolutionRequestBody(BaseModel):
    """POST /v1/resolutions request body."""

    intake_request_id: UUID


class SelectCandidateRequestBody(BaseModel):
    """POST /v1/resolutions/{run_id}/select request body."""

    ehr_code: str


# ---------------------------------------------------------------------------
# Mapper: service result → API response
# ---------------------------------------------------------------------------


def map_result_to_response(result: ResolutionResult) -> ResolutionResponse:
    """Convert a service-layer ResolutionResult to the appropriate Pydantic model.

    The returned type is always one of the three union members, discriminated
    by the status field.
    """
    if result.status == ResolutionStatus.RESOLVED:
        return ResolvedResolutionResponse(
            resolution_run_id=result.resolution_run_id,
            ehr_code=result.ehr_code or "",
            normalized_address=result.normalized_address or "",
            address_aliases=result.address_aliases,
            confidence_score=result.confidence_score or 0.0,
        )

    if result.status == ResolutionStatus.AMBIGUOUS:
        cands = [
            ResolutionCandidate(
                ehr_code=c.ehr_code,
                normalized_address=c.normalized_address or "",
                confidence_score=c.confidence_score,
            )
            for c in result.candidates
        ]
        return AmbiguousResolutionResponse(
            resolution_run_id=result.resolution_run_id,
            candidates=cands,
        )

    # UNRESOLVED
    return UnresolvedResolutionResponse(
        resolution_run_id=result.resolution_run_id,
        candidates=[],
    )
