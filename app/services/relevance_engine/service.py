"""RelevanceEngine — classifies observations into relevance buckets.

Responsibilities (doc 04 §5):
  - classify observations by relevance
  - filter source noise
  - prepare listing_candidate observations for later

The classification policy is a static dict in policy.py sourced from
doc 05's "Practical field policy" section.  No learned model, no DB
lookup — classification is a pure function of (namespace, key).
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observations import Observation
from app.services.relevance_engine.policy import classify
from app.services.relevance_engine.types import ClassificationResult

logger = logging.getLogger(__name__)


class RelevanceEngine:
    """Classifies observations into relevance buckets per doc 05 policy."""

    def classify_observation(self, obs: Observation) -> str:
        """Return the bucket for one observation.

        Inputs:
          obs — an Observation ORM instance (only namespace and key are used).
        Outputs:
          Relevance bucket string.  Pure function of (namespace, key).
        Side effects:
          None.
        """
        return classify(obs.namespace, obs.key)

    async def classify_extraction_run(
        self,
        extraction_run_id: UUID,
        db: AsyncSession,
    ) -> ClassificationResult:
        """Update observations.relevance_class for all rows from this run.

        Inputs:
          extraction_run_id — UUID of the ExtractionRun to classify.
          db                — async SQLAlchemy session (caller owns lifecycle).
        Outputs:
          ClassificationResult with counts per bucket.
        Persistence:
          Updates observations.relevance_class for all matched rows and commits.
        Raises:
          Nothing — returns result with 0 classified if no observations found.

        Idempotent — safe to re-run.  Running twice produces identical bucket
        assignments because the policy is deterministic.
        """
        stmt = select(Observation).where(
            Observation.extraction_run_id == extraction_run_id
        )
        result = await db.execute(stmt)
        observations = list(result.scalars().all())

        bucket_counts: dict[str, int] = {}
        for obs in observations:
            bucket = self.classify_observation(obs)
            obs.relevance_class = bucket
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

        await db.commit()

        logger.info(
            "Classified %d observations for extraction_run %s: %s",
            len(observations), extraction_run_id, bucket_counts,
        )

        return ClassificationResult(
            observations_classified=len(observations),
            bucket_counts=bucket_counts,
        )
