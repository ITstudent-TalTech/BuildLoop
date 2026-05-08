"""POST /v1/projects/{project_id}/passport-drafts
GET  /v1/projects/{project_id}/passport-draft

Matches doc 11 § 4.  Each handler is < 30 lines and delegates to
PassportEngine.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.passport_drafts import PassportDraft
from app.schemas.passport import PassportDraftGenerateResponse, PassportDraftGetResponse
from app.services.passport_engine.service import PassportEngine
from app.services.passport_engine.types import ProjectionResult

router = APIRouter(tags=["passport-drafts"])


@router.post(
    "/projects/{project_id}/passport-drafts",
    response_model=PassportDraftGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate or regenerate the passport draft for a project",
)
async def generate_passport_draft(
    project_id: UUID,
    db: AsyncSession = Depends(get_session),
) -> PassportDraftGenerateResponse:
    """Classify observations and project them into a FieldValue<T>-shaped draft."""
    engine = PassportEngine()
    try:
        result: ProjectionResult = await engine.generate_draft(project_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return PassportDraftGenerateResponse(
        passport_draft_id=result.passport_draft_id,
        schema_version=result.schema_version,
        schema_completeness_score=result.schema_completeness_score,
        confidence_score=result.confidence_score,
    )


@router.get(
    "/projects/{project_id}/passport-draft",
    response_model=PassportDraftGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Return the current passport draft for a project",
)
async def get_passport_draft(
    project_id: UUID,
    db: AsyncSession = Depends(get_session),
) -> PassportDraftGetResponse:
    """Return the full draft payload merged with ORM metadata."""
    engine = PassportEngine()
    draft: PassportDraft | None = await engine.get_current_draft(project_id, db)
    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No passport draft found for project {project_id}. "
                   "Call POST /passport-drafts first.",
        )
    payload = draft.payload_json
    return PassportDraftGetResponse(
        passport_draft_id=draft.id,
        building_id=draft.building_id,
        project_id=draft.project_id,
        schema_version=draft.schema_version,
        status=draft.status,
        generated_at=draft.generated_at.isoformat(),
        identity=payload.get("identity", {}),
        building_profile=payload.get("building_profile", {}),
        structural_systems=payload.get("structural_systems", {}),
        technical_systems=payload.get("technical_systems", {}),
        location=payload.get("location", {}),
        building_parts=payload.get("building_parts", {}),
        quality=payload.get("quality", {}),
    )
