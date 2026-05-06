"""ResolverService — orchestrates address-to-EHR resolution with full persistence.

Workflow per resolve():
  1. Load IntakeRequest; read project_id from intake_requests.project_id FK column.
  2. Normalize the raw address and generate query variants.
  3. Call In-ADS once per variant; merge candidate groups across variants.
  4. Score candidates; decide resolution status.
  5. Persist: ResolverRun + ResolverCandidate rows; update IntakeRequest status.
  6. On resolved: upsert Building row; set Project.building_id.
  7. Return ResolutionResult.

select_candidate() handles the manual pick from an ambiguous run:
  1. Load existing ResolverRun + its candidates.
  2. Verify the chosen ehr_code is among the candidates.
  3. Promote the run to resolved; mark the candidate primary.
  4. Upsert Building; set Project.building_id.
  5. Return resolved ResolutionResult.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.buildings import Building
from app.models.intake_requests import IntakeRequest
from app.models.projects import Project
from app.models.resolver_runs import ResolverCandidate, ResolverRun
from app.services.resolver.candidate_grouper import (
    collect_raw_hits,
    group_candidates,
    merge_variant_groups,
)
from app.services.resolver.confidence import decide_status, score_candidate
from app.services.resolver.inads_adapter import InAdsAdapter
from app.services.resolver.normalizer import normalize_address
from app.services.resolver.query_variants import generate_variants
from app.services.resolver.types import (
    CandidateGroup,
    ResolutionResult,
    ResolutionStatus,
    ResolverThresholds,
)

logger = logging.getLogger(__name__)


class ResolverService:
    """Address-to-EHR resolution service.

    Inject a custom InAdsAdapter for testing; otherwise the default adapter
    is created lazily on first use (so get_settings() is not called at
    class construction time).
    """

    def __init__(self, adapter: InAdsAdapter | None = None) -> None:
        self._adapter = adapter

    def _get_adapter(self) -> InAdsAdapter:
        if self._adapter is None:
            self._adapter = InAdsAdapter()
        return self._adapter

    # ------------------------------------------------------------------
    # resolve
    # ------------------------------------------------------------------

    async def resolve(
        self,
        intake_request_id: UUID,
        db: AsyncSession,
    ) -> ResolutionResult:
        """Resolve an intake request's address to a canonical EHR building code.

        Inputs:
          intake_request_id — UUID of an existing IntakeRequest row.
          db                — async SQLAlchemy session (caller owns the lifecycle).
        Outputs:
          ResolutionResult with status, ehr_code, candidates, etc.
        Persistence:
          - IntakeRequest.status updated: "received" → "resolving" → result.
          - One address_resolution_runs row inserted.
          - N address_resolution_candidates rows inserted (all candidates).
          - On resolved: buildings upserted; project.building_id set.
        Raises:
          ValueError if the intake request is not found.
        """
        settings = get_settings()

        # 1. Load intake
        intake = await db.get(IntakeRequest, intake_request_id)
        if intake is None:
            raise ValueError(f"IntakeRequest {intake_request_id} not found")

        # 2. Read project_id from the FK column (set by IntakeService)
        project_id: UUID | None = intake.project_id
        if project_id is None:
            logger.warning(
                "IntakeRequest %s has no associated project (project_id is None); "
                "building linkage will be skipped.",
                intake_request_id,
            )

        # 3. Mark intake as resolving
        intake.status = "resolving"
        db.add(intake)
        await db.flush()

        # 4. Normalize + variants
        addr = intake.raw_address_input
        normalized = normalize_address(addr)
        variants = generate_variants(normalized)

        # 5. Query In-ADS for each variant; merge groups
        adapter = self._get_adapter()
        all_groups: list[CandidateGroup] = []

        for variant in variants:
            response = await adapter.search(variant.query)
            if not response.ok or not response.data:
                logger.debug(
                    "In-ADS returned no usable data for variant %r: %s",
                    variant.tag,
                    response.error,
                )
                continue
            raw_hits = collect_raw_hits(response.data)
            new_groups = group_candidates(raw_hits, variant)
            all_groups = merge_variant_groups(all_groups, new_groups)

        # 6. Score and sort
        thresholds = ResolverThresholds(
            auto_resolve=settings.resolver_auto_resolve_threshold,
            ambiguous=settings.resolver_ambiguous_threshold,
        )
        scored = [
            score_candidate(normalized, grp, grp.matched_variants)
            for grp in all_groups
        ]
        scored.sort(key=lambda c: c.confidence_score, reverse=True)

        # 7. Decide status
        status = decide_status(scored, thresholds)

        # 8. Derive result fields per status
        resolved_ehr_code: str | None = None
        resolved_address: str | None = None
        resolved_aliases: list[str] = []
        resolved_confidence: float | None = None
        reason: str | None = None

        if status == ResolutionStatus.RESOLVED:
            top = scored[0]
            resolved_ehr_code = top.ehr_code
            resolved_address = top.normalized_address
            resolved_aliases = top.address_aliases
            resolved_confidence = top.confidence_score
        elif status == ResolutionStatus.AMBIGUOUS:
            reason = "multiple_or_weak_candidates"
            if scored:
                resolved_confidence = scored[0].confidence_score
        else:  # UNRESOLVED
            reason = (
                "no_extractable_ehr_code_found" if not scored else "no_reliable_candidate"
            )
            if scored:
                resolved_confidence = scored[0].confidence_score

        # 9. Persist ResolverRun
        variant_dicts = [{"query": v.query, "tag": v.tag} for v in variants]
        run = ResolverRun(
            intake_request_id=intake.id,
            project_id=project_id,
            resolver_version=settings.resolver_version,
            status=status.value,
            resolved_ehr_code=resolved_ehr_code,
            normalized_address=resolved_address,
            address_aliases=resolved_aliases,
            confidence_score=resolved_confidence,
            reason=reason,
            query_variants=variant_dicts,
        )
        db.add(run)
        await db.flush()

        # 10. Persist candidates (all of them, for audit trail)
        for i, cand in enumerate(scored):
            primary = i == 0 and status in {
                ResolutionStatus.RESOLVED,
                ResolutionStatus.AMBIGUOUS,
            }
            rc = ResolverCandidate(
                resolution_run_id=run.id,
                ehr_code=cand.ehr_code,
                normalized_address=cand.normalized_address,
                address_aliases=cand.address_aliases,
                confidence_score=cand.confidence_score,
                object_types=cand.object_types,
                matched_query_variants=[v.tag for v in cand.matched_variants],
                match_reasons=cand.match_reasons,
                primary_candidate=primary,
                raw_candidate=cand.raw_candidate,
            )
            db.add(rc)

        # 11. On resolved: upsert building and link project
        if status == ResolutionStatus.RESOLVED and resolved_ehr_code and project_id:
            building = await self._upsert_building(
                db,
                resolved_ehr_code,
                resolved_address,
                resolved_aliases,
                resolved_confidence,
            )
            project = await db.get(Project, project_id)
            if project:
                project.building_id = building.id
                db.add(project)

        # 12. Finalise intake status
        intake.status = status.value
        db.add(intake)
        await db.commit()

        return ResolutionResult(
            status=status,
            resolution_run_id=run.id,
            ehr_code=resolved_ehr_code,
            normalized_address=resolved_address,
            address_aliases=resolved_aliases,
            confidence_score=resolved_confidence,
            candidates=scored,
            reason=reason,
        )

    # ------------------------------------------------------------------
    # select_candidate
    # ------------------------------------------------------------------

    async def select_candidate(
        self,
        resolution_run_id: UUID,
        ehr_code: str,
        db: AsyncSession,
    ) -> ResolutionResult:
        """Manually promote one candidate from an ambiguous run to resolved.

        Inputs:
          resolution_run_id — UUID of an existing ResolverRun.
          ehr_code          — EHR code string that must exist in the run's candidates.
          db                — async SQLAlchemy session.
        Outputs:
          ResolutionResult with status=RESOLVED.
        Persistence:
          - ResolverRun.status set to "resolved", resolved fields populated.
          - Chosen ResolverCandidate.primary_candidate set True; others False.
          - buildings upserted; project.building_id set.
        Raises:
          ValueError if run not found or ehr_code not among candidates.
        """
        # 1. Load run
        run = await db.get(ResolverRun, resolution_run_id)
        if run is None:
            raise ValueError(f"ResolverRun {resolution_run_id} not found")

        # 2. Load candidates
        stmt = select(ResolverCandidate).where(
            ResolverCandidate.resolution_run_id == resolution_run_id
        )
        result = await db.execute(stmt)
        candidates = list(result.scalars().all())

        # 3. Find the chosen candidate
        chosen = next((c for c in candidates if c.ehr_code == ehr_code), None)
        if chosen is None:
            raise ValueError(
                f"EHR code {ehr_code!r} is not among candidates for run {resolution_run_id}"
            )

        # 4. Update run to resolved
        aliases: list[str] = list(chosen.address_aliases) if chosen.address_aliases else []
        run.status = ResolutionStatus.RESOLVED.value
        run.resolved_ehr_code = ehr_code
        run.normalized_address = chosen.normalized_address
        run.address_aliases = aliases
        run.confidence_score = chosen.confidence_score
        run.reason = None
        db.add(run)

        # 5. Mark primary_candidate
        for c in candidates:
            c.primary_candidate = c.ehr_code == ehr_code
            db.add(c)

        # 6. Upsert building and link project
        confidence = float(chosen.confidence_score) if chosen.confidence_score else None
        building = await self._upsert_building(
            db, ehr_code, chosen.normalized_address, aliases, confidence
        )
        if run.project_id:
            project = await db.get(Project, run.project_id)
            if project:
                project.building_id = building.id
                db.add(project)

        await db.commit()

        return ResolutionResult(
            status=ResolutionStatus.RESOLVED,
            resolution_run_id=resolution_run_id,
            ehr_code=ehr_code,
            normalized_address=chosen.normalized_address,
            address_aliases=aliases,
            confidence_score=confidence,
        )

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    async def _upsert_building(
        self,
        db: AsyncSession,
        ehr_code: str,
        normalized_address: str | None,
        address_aliases: list[str],
        confidence: float | None,
    ) -> Building:
        """Insert or update a Building row keyed on primary_ehr_code.

        Returns the Building instance (with .id populated).
        """
        stmt = select(Building).where(Building.primary_ehr_code == ehr_code)
        result = await db.execute(stmt)
        building = result.scalar_one_or_none()

        if building is None:
            building = Building(
                primary_ehr_code=ehr_code,
                normalized_address=normalized_address,
                address_aliases=address_aliases,
                source_identity_confidence=confidence,
            )
            db.add(building)
            await db.flush()
        else:
            building.normalized_address = normalized_address
            building.address_aliases = address_aliases
            building.source_identity_confidence = confidence
            db.add(building)

        return building
