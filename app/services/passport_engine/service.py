"""PassportEngine — projects observations into a passport draft.

Responsibilities (doc 04 §6):
  - build current draft from passport_core + supporting observations
  - compute quality metrics
  - generate JSON view
  - one draft per project (upsert on each call)

The full pipeline in generate_draft():
  1. Load Project.
  2. Find latest completed ExtractionRun via the project's SourceDocuments.
  3. Classify observations inline if any are 'unclassified'.
  4. Read all observations from that extraction run.
  5. Project to payload_json (pure function).
  6. Compute quality scores and update the quality section.
  7. Upsert passport_drafts row (one per project).
  8. Return ProjectionResult.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.extraction_runs import ExtractionRun
from app.models.observations import Observation
from app.models.passport_drafts import PassportDraft
from app.models.projects import Project
from app.models.source_documents import SourceDocument
from app.services.passport_engine.projection import project_observations_to_passport
from app.services.passport_engine.quality import (
    compute_confidence_score,
    compute_schema_completeness,
    derive_section_breakdown,
    list_missing_fields,
)
from app.services.passport_engine.types import ProjectionResult
from app.services.relevance_engine.policy import classify
from app.services.relevance_engine.service import RelevanceEngine

logger = logging.getLogger(__name__)

_PROJECTED_BUCKETS = frozenset({"passport_core", "passport_supporting"})


class PassportEngine:
    """Orchestrates observation projection and passport draft persistence."""

    async def generate_draft(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> ProjectionResult:
        """Generate or regenerate the passport draft for a project.

        Inputs:
          project_id — UUID of an existing Project row.
          db         — async SQLAlchemy session (caller owns lifecycle).
        Outputs:
          ProjectionResult with draft ID and quality scores.
        Persistence:
          - Updates observations.relevance_class if any are 'unclassified'.
          - Upserts one PassportDraft row (creates or replaces for this project).
        Raises:
          ValueError if the project or a completed extraction run cannot be found.
        """
        settings = get_settings()

        # 1. Load Project
        project: Project | None = await db.get(Project, project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")

        # 2. Find latest completed extraction run via project's source documents
        stmt = (
            select(ExtractionRun)
            .join(SourceDocument, ExtractionRun.source_document_id == SourceDocument.id)
            .where(SourceDocument.project_id == project_id)
            .where(ExtractionRun.status == "completed")
            .order_by(ExtractionRun.completed_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        latest_run: ExtractionRun | None = result.scalar_one_or_none()

        if latest_run is None:
            raise ValueError(
                f"No completed extraction run found for project {project_id}. "
                "Parse the source document first."
            )

        # 3. Load all observations from this extraction run
        obs_stmt = select(Observation).where(
            Observation.extraction_run_id == latest_run.id
        )
        obs_result = await db.execute(obs_stmt)
        all_obs: list[Observation] = list(obs_result.scalars().all())

        # Classify inline if any are still 'unclassified' (idempotent)
        if any(o.relevance_class == "unclassified" for o in all_obs):
            re_engine = RelevanceEngine()
            for obs in all_obs:
                obs.relevance_class = re_engine.classify_observation(obs)
            logger.info(
                "Classified %d observations inline for extraction_run %s",
                len(all_obs), latest_run.id,
            )

        # 4. Load the source document for provenance in FieldSource
        source_doc: SourceDocument | None = await db.get(
            SourceDocument, latest_run.source_document_id
        )

        # 5. Project observations to payload (pure function)
        payload = project_observations_to_passport(all_obs, source_doc)

        # 6. Compute quality scores and update the quality section
        relevant_obs = [o for o in all_obs if o.relevance_class in _PROJECTED_BUCKETS]
        completeness = compute_schema_completeness(payload)
        confidence = compute_confidence_score(relevant_obs, settings)
        conf_label = _derive_confidence_label(confidence)
        section_breakdown = derive_section_breakdown(payload)
        missing = list_missing_fields(payload)

        payload["quality"] = {
            "schema_completeness_score": completeness,
            "confidence_score":          confidence,
            "confidence_label":          conf_label,
            "section_breakdown":         section_breakdown,
            "missing_fields":            missing,
        }

        # 7. Upsert passport_drafts (one per project)
        draft_stmt = select(PassportDraft).where(PassportDraft.project_id == project_id)
        draft_result = await db.execute(draft_stmt)
        draft: PassportDraft | None = draft_result.scalar_one_or_none()

        now = datetime.now(tz=timezone.utc)
        if draft is None:
            draft = PassportDraft(
                building_id=project.building_id,
                project_id=project_id,
                schema_version="buildloop.passport.mvp.v1",
                status="draft_system_generated",
                payload_json=payload,
                schema_completeness_score=completeness,
                confidence_score=confidence,
                generated_at=now,
            )
            db.add(draft)
        else:
            draft.payload_json = payload
            draft.schema_completeness_score = completeness
            draft.confidence_score = confidence
            draft.generated_at = now

        await db.commit()
        await db.refresh(draft)

        logger.info(
            "Passport draft upserted for project %s: completeness=%.1f%%, "
            "confidence=%.1f%%, draft_id=%s",
            project_id, completeness, confidence, draft.id,
        )

        return ProjectionResult(
            passport_draft_id=draft.id,
            schema_version=draft.schema_version,
            schema_completeness_score=float(draft.schema_completeness_score or 0.0),
            confidence_score=float(draft.confidence_score or 0.0),
            building_id=project.building_id,
            project_id=project_id,
            status=draft.status,
            generated_at=now.isoformat(),
            payload_json=payload,
        )

    async def get_current_draft(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> PassportDraft | None:
        """Return the current passport draft for a project, or None.

        Inputs:
          project_id — UUID of the Project.
          db         — async SQLAlchemy session.
        Outputs:
          PassportDraft ORM row or None if no draft exists.
        Side effects:
          Read-only.
        """
        stmt = select(PassportDraft).where(PassportDraft.project_id == project_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _derive_confidence_label(score: float) -> str:
    """Map a 0-100 confidence_score to a label."""
    if score >= 90.0:
        return "high"
    if score >= 65.0:
        return "medium"
    return "low"
