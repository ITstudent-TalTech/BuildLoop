"""POST /v1/resolutions — run address resolution for an intake request.
POST /v1/resolutions/{resolution_run_id}/select — manually pick a candidate.

Matches doc 11 § 1 and /web/lib/api/types.ts ResolutionResponse exactly.
The response is a discriminated union on the "status" field.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.resolution import (
    ResolutionRequestBody,
    ResolutionResponse,
    SelectCandidateRequestBody,
    map_result_to_response,
)
from app.services.resolver.service import ResolverService

router = APIRouter(prefix="/resolutions", tags=["resolution"])


@router.post(
    "",
    response_model=ResolutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run address resolution for an intake request",
)
async def run_resolution(
    body: ResolutionRequestBody,
    db: AsyncSession = Depends(get_session),
) -> ResolutionResponse:
    """Resolve intake_request_id → EHR code via In-ADS gazetteer."""
    try:
        svc = ResolverService()
        result = await svc.resolve(body.intake_request_id, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"resolution_failed: {exc}",
        ) from exc

    return map_result_to_response(result)


@router.post(
    "/{resolution_run_id}/select",
    response_model=ResolutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Manually select a candidate from an ambiguous resolution",
)
async def select_candidate(
    resolution_run_id: UUID,
    body: SelectCandidateRequestBody,
    db: AsyncSession = Depends(get_session),
) -> ResolutionResponse:
    """Promote one candidate from an ambiguous run to resolved status."""
    try:
        svc = ResolverService()
        result = await svc.select_candidate(resolution_run_id, body.ehr_code, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"select_failed: {exc}",
        ) from exc

    return map_result_to_response(result)
