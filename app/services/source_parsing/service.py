"""SourceParsingService — orchestrates PDF parsing and observation persistence.

Workflow for parse_source_document():
  1. Load SourceDocument by id. Return 'source_not_found' if missing.
  2. Verify parser_status == 'fetched'. Return 'wrong_status' otherwise.
  3. Download PDF bytes from Supabase Storage.
  4. Insert ExtractionRun with status='running'.
  5. Call text_extractor.extract_text(). On failure update run → 'failed'.
  6. Build page_map; call all 6 extractors. Collect ObservationDrafts.
  7. Persist one Observation row per draft.
  8. Update ExtractionRun → 'completed', SourceDocument → 'parsed'. Commit.
  9. Return ParseResult(status='ok', observation_count=N).

Re-parsing is allowed: each call creates a new ExtractionRun. Previous
observations are preserved. Track 2.5 uses the latest extraction_run_id
when projecting; older runs are kept for audit.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.extraction_runs import ExtractionRun
from app.models.observations import Observation
from app.models.source_documents import SourceDocument
from app.services.source_parsing import storage as storage_module
from app.services.source_parsing.extractors import (
    extract_building_parts,
    extract_building_profile,
    extract_identity,
    extract_location,
    extract_structural_systems,
    extract_technical_systems,
)
from app.services.source_parsing.page_map import build_page_map
from app.services.source_parsing.text_extractor import extract_text
from app.services.source_parsing.types import ObservationDraft, ParseResult

logger = logging.getLogger(__name__)

_PARSER_NAME = "source_parsing.v1"


class SourceParsingService:
    """Orchestrates EHR PDF parsing and canonical observation persistence."""

    async def parse_source_document(
        self,
        source_document_id: UUID,
        db: AsyncSession,
        storage_client: Any | None = None,
    ) -> ParseResult:
        """Parse an EHR PDF and persist canonical observations.

        Inputs:
          source_document_id — UUID of a SourceDocument row.
          db                 — async SQLAlchemy session (caller owns lifecycle).
          storage_client     — optional async callable (bucket, path) → bytes
                               for testing; None uses Supabase Storage.
        Outputs:
          ParseResult with status, extraction_run_id, observation_count.
        Persistence:
          - Inserts one ExtractionRun row per call.
          - Inserts N Observation rows (one per extracted field).
          - Updates SourceDocument.parser_status → 'parsed' on success.
        Raises:
          Nothing — all errors are captured in ParseResult.
        """
        settings = get_settings()

        # 1. Load SourceDocument
        doc: SourceDocument | None = await db.get(SourceDocument, source_document_id)
        if doc is None:
            return ParseResult(
                status="source_not_found",
                error=f"source_document {source_document_id} not found",
            )

        # 2. Verify status
        if doc.parser_status != "fetched":
            return ParseResult(
                status="wrong_status",
                error=(
                    f"expected parser_status='fetched', got '{doc.parser_status}'. "
                    "Fetch the source document before parsing."
                ),
            )

        # 3. Download PDF bytes — verify storage coordinates are set
        if not doc.storage_bucket or not doc.storage_path:
            return ParseResult(
                status="parse_failed",
                error="source_document has no storage_bucket or storage_path",
            )
        download = storage_client or storage_module.download_source_pdf
        try:
            pdf_bytes = await download(doc.storage_bucket, doc.storage_path)
        except Exception as exc:
            logger.error(
                "Storage download failed for source_document %s: %s",
                source_document_id, exc,
            )
            return ParseResult(
                status="parse_failed",
                error=f"storage_download_failed: {exc}",
            )

        # 4. Insert ExtractionRun — generate UUID explicitly (same pattern as
        # source_ingestion._new_uuid()) so run_id is available before flush.
        from uuid import uuid4

        now = datetime.now(tz=timezone.utc)
        run_id: UUID = uuid4()
        run = ExtractionRun(
            id=run_id,
            source_document_id=source_document_id,
            parser_name=_PARSER_NAME,
            parser_version=settings.parser_version,
            status="running",
            started_at=now,
        )
        db.add(run)
        await db.flush()

        # 5. Extract text
        try:
            extracted = extract_text(pdf_bytes)
        except Exception as exc:
            logger.error(
                "Text extraction failed for source_document %s: %s",
                source_document_id, exc,
            )
            run.status = "failed"
            run.error_summary = str(exc)[:500]
            run.completed_at = datetime.now(tz=timezone.utc)
            await db.commit()
            return ParseResult(
                status="parse_failed",
                extraction_run_id=run_id,
                error=f"text_extraction_failed: {exc}",
            )

        logger.info(
            "Extracted %d pages via %s for source_document %s",
            extracted.page_count, extracted.method, source_document_id,
        )

        # 6. Build page map and run all extractors
        page_map = build_page_map(extracted.text)
        full_text = extracted.text

        all_drafts: list[ObservationDraft] = []
        all_drafts.extend(extract_identity(page_map))
        all_drafts.extend(extract_building_profile(page_map))
        all_drafts.extend(extract_structural_systems(page_map))
        all_drafts.extend(extract_technical_systems(page_map))
        all_drafts.extend(extract_location(page_map))
        all_drafts.extend(extract_building_parts(full_text))

        # 7. Persist observations
        for draft in all_drafts:
            obs = Observation(
                building_id=doc.building_id,
                project_id=doc.project_id,
                source_document_id=source_document_id,
                extraction_run_id=run_id,
                namespace=draft.namespace,
                key=draft.key,
                section=draft.section,
                value_json=draft.value,  # type: ignore[assignment]
                unit=draft.unit,
                relevance_class=draft.relevance_class,
                confidence_score=draft.confidence_score,
                confidence_label=draft.confidence_label,
                evidence_text=draft.evidence_text,
                page_number=draft.page_number,
                source_locator=draft.source_locator,
            )
            db.add(obs)

        # 8. Update ExtractionRun and SourceDocument
        completed_at = datetime.now(tz=timezone.utc)
        run.status = "completed"
        run.completed_at = completed_at
        doc.parser_status = "parsed"

        await db.commit()

        logger.info(
            "Parsed source_document %s: %d observations, extraction_run %s",
            source_document_id, len(all_drafts), run_id,
        )

        return ParseResult(
            status="ok",
            extraction_run_id=run_id,
            observation_count=len(all_drafts),
            observations=all_drafts,
        )

    async def list_observations(
        self,
        project_id: UUID,
        db: AsyncSession,
        *,
        section: str | None = None,
        relevance_class: str | None = None,
        namespace: str | None = None,
        key: str | None = None,
    ) -> list[Observation]:
        """Return observations for a project, with optional filters.

        Inputs:
          project_id      — UUID of a Project row.
          db              — async SQLAlchemy session.
          section         — optional filter by section.
          relevance_class — optional filter by relevance_class.
          namespace       — optional filter by namespace.
          key             — optional filter by key.
        Outputs:
          list[Observation] ordered by namespace, key (may be empty).
        Side effects:
          Read-only.
        """
        stmt = select(Observation).where(Observation.project_id == project_id)
        if section is not None:
            stmt = stmt.where(Observation.section == section)
        if relevance_class is not None:
            stmt = stmt.where(Observation.relevance_class == relevance_class)
        if namespace is not None:
            stmt = stmt.where(Observation.namespace == namespace)
        if key is not None:
            stmt = stmt.where(Observation.key == key)
        stmt = stmt.order_by(Observation.namespace, Observation.key)
        result = await db.execute(stmt)
        return list(result.scalars().all())
