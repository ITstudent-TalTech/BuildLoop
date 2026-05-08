"""POST /v1/projects/{project_id}/passport-pipeline

Consolidated pipeline: source-fetch → source-parse → passport-project in sequence.
Each stage short-circuits on failure, preserving whatever was written for audit.
Intended for the frontend's resolved-state transition (Session B).

DO NOT remove the four constituent endpoints — they remain for retry/debug/admin.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.extraction_runs import ExtractionRun
from app.models.observations import Observation
from app.schemas.passport_pipeline import (
    PipelineFailureResponse,
    PipelineRequest,
    PipelineSuccessResponse,
)
from app.services.passport_engine.service import PassportEngine
from app.services.source_ingestion.service import SourceIngestionService
from app.services.source_parsing.service import SourceParsingService

router = APIRouter(prefix="/projects", tags=["passport-pipeline"])


@router.post("/{project_id}/passport-pipeline")
async def passport_pipeline(
    project_id: UUID,
    body: PipelineRequest,
    db: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Fetch → parse → project in sequence; short-circuits on first failure."""

    # ── Stage 1: fetch ────────────────────────────────────────────────────────
    fetch_result = await SourceIngestionService().fetch_for_project(
        project_id, body.ehr_code, db
    )
    if fetch_result.status == "fetch_failed":
        return _fail(
            502,
            PipelineFailureResponse(
                status="fetch_failed",
                stage="fetch",
                error=fetch_result.error or "EHR fetch failed",
                source_document_id=fetch_result.source_document_id,
                extraction_run_id=None,
            ),
        )

    source_document_id: UUID = fetch_result.source_document_id  # type: ignore[assignment]
    fetch_status = fetch_result.fetch_status  # "ok" | "deduped"

    # ── Stage 2: parse (skip if deduped + already completed) ─────────────────
    extraction_run_id: UUID | None = None
    observation_count: int = 0

    if fetch_status == "deduped":
        existing_run = await _latest_completed_run(source_document_id, db)
        if existing_run is not None:
            extraction_run_id = existing_run.id
            observation_count = await _count_observations(extraction_run_id, db)

    if extraction_run_id is None:
        parse_result = await SourceParsingService().parse_source_document(
            source_document_id, db
        )
        if parse_result.status != "ok":
            return _fail(
                502,
                PipelineFailureResponse(
                    status="parse_failed",
                    stage="parse",
                    error=parse_result.error or "parsing failed",
                    source_document_id=source_document_id,
                    extraction_run_id=None,
                ),
            )
        extraction_run_id = parse_result.extraction_run_id  # type: ignore[assignment]
        observation_count = parse_result.observation_count

    # Unreachable in practice (successful parse always has an extraction_run_id),
    # but narrows the type for mypy and guards against a broken service contract.
    if extraction_run_id is None:
        return _fail(
            500,
            PipelineFailureResponse(
                status="parse_failed",
                stage="parse",
                error="internal: parse returned ok but no extraction_run_id",
                source_document_id=source_document_id,
                extraction_run_id=None,
            ),
        )

    # ── Stage 3: project ──────────────────────────────────────────────────────
    try:
        projection = await PassportEngine().generate_draft(project_id, db)
    except Exception as exc:
        return _fail(
            500,
            PipelineFailureResponse(
                status="projection_failed",
                stage="project",
                error=str(exc),
                source_document_id=source_document_id,
                extraction_run_id=extraction_run_id,
            ),
        )

    return JSONResponse(
        status_code=200,
        content=PipelineSuccessResponse(
            source_document_id=source_document_id,
            extraction_run_id=extraction_run_id,
            passport_draft_id=projection.passport_draft_id,
            schema_version=projection.schema_version,
            schema_completeness_score=projection.schema_completeness_score,
            confidence_score=projection.confidence_score,
            fetch_status=fetch_status,  # type: ignore[arg-type]
            observation_count=observation_count,
        ).model_dump(mode="json"),
    )


# ── Private helpers ────────────────────────────────────────────────────────────


async def _latest_completed_run(
    source_document_id: UUID,
    db: AsyncSession,
) -> ExtractionRun | None:
    """Return the latest completed ExtractionRun for a source document, or None."""
    stmt = (
        select(ExtractionRun)
        .where(ExtractionRun.source_document_id == source_document_id)
        .where(ExtractionRun.status == "completed")
        .order_by(ExtractionRun.completed_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _count_observations(extraction_run_id: UUID, db: AsyncSession) -> int:
    """Count observations linked to a given extraction run."""
    stmt = (
        select(func.count())
        .select_from(Observation)
        .where(Observation.extraction_run_id == extraction_run_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one() or 0


def _fail(status_code: int, body: PipelineFailureResponse) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
