"""Internal type definitions for the source_parsing service.

ObservationDraft — what extractors produce before DB persistence.
ParseResult     — what SourceParsingService returns to the API layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class ObservationDraft:
    """One parsed field ready to be persisted as an Observation row.

    Maps 1:1 to the observations table columns (doc 03 canonical schema).
    relevance_class is always 'unclassified' until Track 2.5 classifies it.
    """

    namespace: str
    key: str
    section: str
    value: object  # stored as value_json (JSONB); may be str, float, list, dict
    unit: str | None = None
    confidence_score: float | None = None
    confidence_label: str | None = "high"
    evidence_text: str | None = None
    page_number: int | None = None
    source_locator: str | None = None
    relevance_class: str = "unclassified"


@dataclass
class ParseResult:
    """Result returned by SourceParsingService.parse_source_document()."""

    status: str
    """'ok' | 'source_not_found' | 'wrong_status' | 'parse_failed'"""

    extraction_run_id: UUID | None = None
    observation_count: int = 0
    observations: list[ObservationDraft] | None = None
    error: str | None = None
