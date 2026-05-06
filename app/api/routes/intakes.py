"""POST /v1/intakes — create a new intake request and project.

Matches doc 11 § 1 and /web/lib/api/types.ts IntakeResponse exactly.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.intake import IntakeRequestBody, IntakeResponse
from app.services.intake.service import IntakeService

router = APIRouter(prefix="/intakes", tags=["intake"])


@router.post(
    "",
    response_model=IntakeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new intake request",
)
async def create_intake(
    body: IntakeRequestBody,
    db: AsyncSession = Depends(get_session),
) -> IntakeResponse:
    """Accept a raw address and project title; persist intake + project rows."""
    try:
        svc = IntakeService()
        created = await svc.create(body.address_input, body.project_title, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"intake_creation_failed: {exc}",
        ) from exc

    return IntakeResponse(
        intake_request_id=created.intake_request_id,
        project_id=created.project_id,
        status="received",
    )
