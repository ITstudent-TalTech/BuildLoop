"""Internal type definitions for the relevance_engine service."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    """Summary returned by RelevanceEngine.classify_extraction_run()."""

    observations_classified: int
    bucket_counts: dict[str, int] = field(default_factory=dict)
