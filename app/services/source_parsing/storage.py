"""Thin storage wrapper for source_parsing — downloads PDF bytes from Supabase.

The service calls download_source_pdf() with (bucket, path) from the
source_documents row. In tests this module is patched to return fixture bytes.
"""

from __future__ import annotations

from app.core.storage import download_source_document


async def download_source_pdf(bucket: str, path: str) -> bytes:
    """Download a source document PDF from Supabase Storage.

    Inputs:
      bucket — Supabase Storage bucket name (e.g. "source-documents").
      path   — Object path within the bucket.
    Outputs:
      Raw PDF bytes.
    Raises:
      Whatever app.core.storage.download_source_document raises on error.
    """
    return await download_source_document(bucket, path)
