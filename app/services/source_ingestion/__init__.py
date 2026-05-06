"""source_ingestion — EHR PDF fetching, Supabase Storage upload, and checksum dedup."""

from app.services.source_ingestion.service import SourceIngestionService
from app.services.source_ingestion.types import FetchResult, SourceDocumentSummary

__all__ = ["SourceIngestionService", "FetchResult", "SourceDocumentSummary"]
