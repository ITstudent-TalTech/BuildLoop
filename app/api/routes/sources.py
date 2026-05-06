"""POST /v1/projects/{project_id}/sources/fetch — fetch and ingest EHR PDF.
GET  /v1/projects/{project_id}/sources      — list source documents.

Matches doc 11 § 2 and /web/lib/api/types.ts SourceFetchResponse exactly.
Each handler is < 30 lines and delegates entirely to SourceIngestionService.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.source import (
    SourceDocumentSummaryResponse,
    SourceFetchRequest,
    SourceFetchResponse,
)
from app.services.source_ingestion.service import SourceIngestionService
from app.services.source_ingestion.types import FetchResult, SourceDocumentSummary

router = APIRouter(prefix="/projects", tags=["sources"])


@router.post(
    "/{project_id}/sources/fetch",
    response_model=SourceFetchResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch and ingest an EHR PDF for the resolved building",
)
async def fetch_sources(
    project_id: UUID,
    body: SourceFetchRequest,
    db: AsyncSession = Depends(get_session),
) -> SourceFetchResponse:
    """Fetch the EHR PDF for project_id and persist it to Supabase Storage."""
    try:
        svc = SourceIngestionService()
        result: FetchResult = await svc.fetch_for_project(project_id, body.ehr_code, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"source_ingestion_failed: {exc}",
        ) from exc

    if result.status == "project_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error or "project not found",
        )

    return SourceFetchResponse(
        status=result.status,
        source_document_id=result.source_document_id,
        source_type=result.source_type,
        fetch_status=result.fetch_status,
        error=result.error,
    )


@router.get(
    "/{project_id}/sources",
    response_model=list[SourceDocumentSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List source documents for a project",
)
async def list_sources(
    project_id: UUID,
    db: AsyncSession = Depends(get_session),
) -> list[SourceDocumentSummaryResponse]:
    """Return all source documents associated with the given project."""
    try:
        svc = SourceIngestionService()
        summaries: list[SourceDocumentSummary] = await svc.list_for_project(project_id, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"list_sources_failed: {exc}",
        ) from exc

    return [
        SourceDocumentSummaryResponse(
            source_document_id=s.source_document_id,
            source_type=s.source_type,
            source_uri=s.source_uri,
            mime_type=s.mime_type,
            checksum=s.checksum,
            fetched_at=s.fetched_at,
            parser_status=s.parser_status,
            storage_bucket=s.storage_bucket,
            storage_path=s.storage_path,
        )
        for s in summaries
    ]
