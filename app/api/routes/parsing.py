"""POST /v1/source-documents/{source_document_id}/parse
GET  /v1/projects/{project_id}/observations

Matches doc 11 § 3. Each handler is < 30 lines and delegates to
SourceParsingService.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.observations import Observation
from app.schemas.observation import ObservationSummary, ParseResponse
from app.services.source_parsing.service import SourceParsingService
from app.services.source_parsing.types import ParseResult

router = APIRouter(tags=["parsing"])


@router.post(
    "/source-documents/{source_document_id}/parse",
    response_model=ParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Run parser over a source document and persist observations",
)
async def parse_source_document(
    source_document_id: UUID,
    db: AsyncSession = Depends(get_session),
) -> ParseResponse:
    """Parse the EHR PDF for source_document_id and emit canonical observations."""
    svc = SourceParsingService()
    result: ParseResult = await svc.parse_source_document(source_document_id, db)
    return ParseResponse(
        status=result.status,
        extraction_run_id=result.extraction_run_id,
        observation_count=result.observation_count,
        error=result.error,
    )


@router.get(
    "/projects/{project_id}/observations",
    response_model=list[ObservationSummary],
    status_code=status.HTTP_200_OK,
    summary="List observations for a project",
)
async def list_observations(
    project_id: UUID,
    section: str | None = Query(default=None),
    relevance_class: str | None = Query(default=None),
    namespace: str | None = Query(default=None),
    key: str | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
) -> list[ObservationSummary]:
    """Return all observations for the project, optionally filtered."""
    svc = SourceParsingService()
    rows: list[Observation] = await svc.list_observations(
        project_id, db,
        section=section,
        relevance_class=relevance_class,
        namespace=namespace,
        key=key,
    )
    return [_to_summary(r) for r in rows]


def _to_summary(obs: Observation) -> ObservationSummary:
    return ObservationSummary(
        observation_id=obs.id,
        building_id=obs.building_id,
        project_id=obs.project_id,
        source_document_id=obs.source_document_id,
        extraction_run_id=obs.extraction_run_id,
        namespace=obs.namespace,
        key=obs.key,
        section=obs.section,
        value_json=obs.value_json,
        unit=obs.unit,
        relevance_class=obs.relevance_class,
        confidence_score=float(obs.confidence_score) if obs.confidence_score is not None else None,
        confidence_label=obs.confidence_label,
        evidence_text=obs.evidence_text,
        page_number=obs.page_number,
        source_locator=obs.source_locator,
        created_at=obs.created_at,
    )
