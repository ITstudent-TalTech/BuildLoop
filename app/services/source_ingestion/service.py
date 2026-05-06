"""SourceIngestionService — orchestrates EHR PDF fetching and persistence.

Workflow for fetch_for_project():
  1. Load Project. 404 if not found; 400 if building_id is not yet set.
  2. Call EhrFetcher.fetch_pdf(ehr_code). On non-ok result, persist
     a source_documents row with parser_status='fetch_failed' and return
     the failure shape (so errors are reproducible and diagnosable).
  3. Check dedup: find_existing_by_checksum(building_id, checksum).
     If found, return the existing source_document_id with fetch_status='deduped'.
     Dedup happens BEFORE upload to avoid wasting storage quota.
  4. Upload PDF bytes to Supabase Storage.
  5. Insert source_documents row with full metadata.
  6. Return FetchResult(status='ok', fetch_status='ok').

Workflow for list_for_project():
  Query source_documents where project_id matches, return summaries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projects import Project
from app.models.source_documents import SourceDocument
from app.services.source_ingestion import dedup as dedup_module
from app.services.source_ingestion import storage as storage_module
from app.services.source_ingestion.ehr_fetcher import EhrFetcher
from app.services.source_ingestion.types import (
    EhrFetchResult,
    FetchResult,
    SourceDocumentSummary,
)

logger = logging.getLogger(__name__)

_SOURCE_TYPE = "ehr_pdf"
_MIME_TYPE = "application/pdf"


class SourceIngestionService:
    """Orchestrates EHR PDF fetching, deduplication, storage, and persistence.

    Inject a custom EhrFetcher for testing; otherwise the default fetcher
    is created lazily on first use.
    """

    def __init__(self, fetcher: EhrFetcher | None = None) -> None:
        self._fetcher = fetcher

    def _get_fetcher(self) -> EhrFetcher:
        if self._fetcher is None:
            self._fetcher = EhrFetcher()
        return self._fetcher

    async def fetch_for_project(
        self,
        project_id: UUID,
        ehr_code: str,
        db: AsyncSession,
    ) -> FetchResult:
        """Fetch an EHR PDF for the given project and persist it.

        Inputs:
          project_id — UUID of an existing Project row.
          ehr_code   — Estonian EHR building identifier.
          db         — async SQLAlchemy session (caller owns lifecycle).
        Outputs:
          FetchResult with status, source_document_id, source_type, fetch_status.
        Persistence:
          - On any outcome: a source_documents row is inserted.
          - On fetch_failed: parser_status='fetch_failed', error in fetch_metadata.
          - On deduped: no new row; existing source_document_id is returned.
          - On success: new row with parser_status='fetched' + Storage object.
        Raises:
          Nothing — all errors are captured in FetchResult.
        """
        # 1. Load project
        project = await db.get(Project, project_id)
        if project is None:
            return FetchResult(
                status="project_not_found",
                source_document_id=None,
                source_type=_SOURCE_TYPE,
                fetch_status="failed",
                error=f"project {project_id} not found",
            )

        if project.building_id is None:
            return FetchResult(
                status="project_not_resolved",
                source_document_id=None,
                source_type=_SOURCE_TYPE,
                fetch_status="failed",
                error="project has no resolved building; run resolution first",
            )

        building_id: UUID = project.building_id

        # 2. Fetch PDF
        fetcher = self._get_fetcher()
        fetch_result: EhrFetchResult = await fetcher.fetch_pdf(ehr_code)

        if not fetch_result.ok:
            doc = await self._persist_failed(
                db,
                project_id=project_id,
                building_id=building_id,
                source_uri=fetch_result.source_uri,
                fetch_result=fetch_result,
            )
            return FetchResult(
                status="fetch_failed",
                source_document_id=doc.id,
                source_type=_SOURCE_TYPE,
                fetch_status="failed",
                error=fetch_result.error,
            )

        # 3. Dedup check (BEFORE upload to avoid wasting storage quota)
        assert fetch_result.checksum is not None
        existing = await dedup_module.find_existing_by_checksum(
            building_id=building_id,
            checksum=fetch_result.checksum,
            db=db,
        )
        if existing is not None:
            logger.info(
                "Dedup hit for building %s checksum %s — returning existing doc %s",
                building_id,
                fetch_result.checksum[:12],
                existing.id,
            )
            return FetchResult(
                status="ok",
                source_document_id=existing.id,
                source_type=_SOURCE_TYPE,
                fetch_status="deduped",
            )

        # 4. Upload to Supabase Storage
        assert fetch_result.content is not None
        source_doc_id = _new_uuid()
        storage_bucket, storage_path = await storage_module.upload_ehr_pdf(
            building_id=building_id,
            source_document_id=source_doc_id,
            content=fetch_result.content,
        )

        # 5. Persist source_documents row
        now = datetime.now(tz=timezone.utc)
        doc = SourceDocument(
            id=source_doc_id,
            building_id=building_id,
            project_id=project_id,
            source_type=_SOURCE_TYPE,
            source_uri=fetch_result.source_uri,
            mime_type=_MIME_TYPE,
            checksum=fetch_result.checksum,
            fetched_at=now,
            parser_status="fetched",
            storage_bucket=storage_bucket,
            storage_path=storage_path,
            fetch_metadata=fetch_result.fetch_metadata,
        )
        db.add(doc)
        await db.commit()

        logger.info(
            "Source document %s ingested for project %s (building %s)",
            source_doc_id,
            project_id,
            building_id,
        )

        return FetchResult(
            status="ok",
            source_document_id=source_doc_id,
            source_type=_SOURCE_TYPE,
            fetch_status="ok",
        )

    async def list_for_project(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> list[SourceDocumentSummary]:
        """Return all source documents associated with a project.

        Inputs:
          project_id — UUID of a Project row (existence not verified).
          db         — async SQLAlchemy session.
        Outputs:
          List of SourceDocumentSummary (may be empty).
        Side effects:
          Read-only.
        """
        stmt = select(SourceDocument).where(
            SourceDocument.project_id == project_id
        )
        result = await db.execute(stmt)
        rows = list(result.scalars().all())
        return [_to_summary(row) for row in rows]

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    async def _persist_failed(
        self,
        db: AsyncSession,
        *,
        project_id: UUID,
        building_id: UUID,
        source_uri: str,
        fetch_result: EhrFetchResult,
    ) -> SourceDocument:
        """Persist a fetch_failed source_documents row and commit."""
        now = datetime.now(tz=timezone.utc)
        doc = SourceDocument(
            building_id=building_id,
            project_id=project_id,
            source_type=_SOURCE_TYPE,
            source_uri=source_uri,
            mime_type=_MIME_TYPE,
            fetched_at=now,
            parser_status="fetch_failed",
            fetch_metadata={
                **fetch_result.fetch_metadata,
                "error": fetch_result.error,
                "ssl_fallback_used": fetch_result.ssl_fallback_used,
            },
        )
        db.add(doc)
        await db.commit()
        return doc


def _new_uuid() -> UUID:
    """Isolated for easy mocking in tests."""
    from uuid import uuid4
    return uuid4()


def _to_summary(doc: SourceDocument) -> SourceDocumentSummary:
    return SourceDocumentSummary(
        source_document_id=doc.id,
        source_type=doc.source_type,
        source_uri=doc.source_uri,
        mime_type=doc.mime_type,
        checksum=doc.checksum,
        fetched_at=doc.fetched_at,
        parser_status=doc.parser_status,
        storage_bucket=doc.storage_bucket,
        storage_path=doc.storage_path,
    )
