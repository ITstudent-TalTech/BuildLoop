"""Thin wrapper around app.core.storage for source-ingestion-specific uploads.

Decides the storage path convention and MIME type, then delegates to the
shared Supabase Storage client. Does not reimplement storage interaction.

Storage path: {building_id}/{source_document_id}.pdf
Bucket:       settings.supabase_storage_source_bucket (default: "source-documents")
"""

from __future__ import annotations

from uuid import UUID

from app.core.config import get_settings
from app.core.storage import upload_source_document


async def upload_ehr_pdf(
    building_id: UUID,
    source_document_id: UUID,
    content: bytes,
) -> tuple[str, str]:
    """Upload an EHR PDF to Supabase Storage.

    Inputs:
      building_id        — UUID of the Building row (used in the storage path).
      source_document_id — UUID of the SourceDocument row (used in the storage path).
      content            — raw PDF bytes.
    Outputs:
      (storage_bucket, storage_path) — both are persisted on the source_documents row.
    Raises:
      Whatever app.core.storage.upload_source_document raises on Supabase error.
    """
    settings = get_settings()
    storage_path = await upload_source_document(
        building_id=building_id,
        source_document_id=source_document_id,
        content=content,
        mime_type="application/pdf",
    )
    return settings.supabase_storage_source_bucket, storage_path
