"""Relevance engine — classifies observations into relevance buckets.

Public API:
  RelevanceEngine        — service class for classify_observation / classify_extraction_run
  ClassificationResult   — result dataclass returned by classify_extraction_run
  RelevancePolicy        — alias for the policy module (for callers that need
                           the raw FIELD_RELEVANCE_MAP or classify() helper)
"""

from app.services.relevance_engine import policy as RelevancePolicy
from app.services.relevance_engine.service import RelevanceEngine
from app.services.relevance_engine.types import ClassificationResult

__all__ = ["RelevanceEngine", "ClassificationResult", "RelevancePolicy"]
