"""Supabase Storage client wrappers.

Storage path convention:
  source documents : {building_id}/{source_document_id}.{ext}
  published passports: {building_id}/{passport_version_id}.pdf

Access semantics:
  - Uploads use the service-role key (server context, bypasses RLS).
  - Signed URLs are generated with the service-role key and expire
    after `expires_in` seconds (default 1 hour).
  - Callers never hold a long-lived public URL; all access is via
    short-lived signed URLs.

The Supabase Python client is synchronous. All public functions here
run the sync calls in a thread-pool executor via asyncio.to_thread()
so they are safe to await in FastAPI route handlers.
"""

import asyncio
from uuid import UUID

from supabase import Client, create_client

from app.core.config import get_settings


def _get_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _sync_upload(bucket: str, path: str, content: bytes, mime_type: str) -> str:
    client = _get_client()
    client.storage.from_(bucket).upload(
        path=path,
        file=content,
        file_options={"content-type": mime_type, "upsert": "false"},
    )
    return path


def _sync_signed_url(bucket: str, path: str, expires_in: int) -> str:
    client = _get_client()
    result = client.storage.from_(bucket).create_signed_url(path, expires_in)
    signed_url = result.get("signedURL") or result.get("signedUrl", "")
    return str(signed_url)


def _sync_list_buckets() -> list[dict[str, object]]:
    client = _get_client()
    return client.storage.list_buckets()  # type: ignore[return-value]


def _sync_get_bucket_names() -> list[str]:
    client = _get_client()
    buckets = client.storage.list_buckets()
    names: list[str] = []
    for b in buckets:
        # supabase-py v2 returns Bucket objects; v1 returned dicts
        if hasattr(b, "name"):
            names.append(str(b.name))
        elif isinstance(b, dict):
            names.append(str(b.get("name", "")))
    return [n for n in names if n]


async def upload_source_document(
    building_id: UUID,
    source_document_id: UUID,
    content: bytes,
    mime_type: str,
) -> str:
    """Upload a raw source PDF to the source-documents bucket.

    Returns the storage key (path within the bucket).
    Path format: {building_id}/{source_document_id}.{ext}
    """
    settings = get_settings()
    ext = "pdf" if mime_type == "application/pdf" else mime_type.split("/")[-1]
    path = f"{building_id}/{source_document_id}.{ext}"
    return await asyncio.to_thread(
        _sync_upload, settings.supabase_storage_source_bucket, path, content, mime_type
    )


async def get_source_document_url(storage_key: str, expires_in: int = 3600) -> str:
    """Return a short-lived signed URL for a source document.

    Args:
        storage_key: The path returned by upload_source_document.
        expires_in: URL validity in seconds (default 1 hour).
    """
    settings = get_settings()
    return await asyncio.to_thread(
        _sync_signed_url,
        settings.supabase_storage_source_bucket,
        storage_key,
        expires_in,
    )


async def upload_published_passport(
    building_id: UUID,
    passport_version_id: UUID,
    content: bytes,
) -> str:
    """Upload a generated passport PDF to the published-passports bucket.

    Returns the storage key (path within the bucket).
    Path format: {building_id}/{passport_version_id}.pdf
    """
    settings = get_settings()
    path = f"{building_id}/{passport_version_id}.pdf"
    return await asyncio.to_thread(
        _sync_upload,
        settings.supabase_storage_passport_bucket,
        path,
        content,
        "application/pdf",
    )


async def get_published_passport_url(storage_key: str, expires_in: int = 3600) -> str:
    """Return a short-lived signed URL for a published passport PDF.

    Args:
        storage_key: The path returned by upload_published_passport.
        expires_in: URL validity in seconds (default 1 hour).
    """
    settings = get_settings()
    return await asyncio.to_thread(
        _sync_signed_url,
        settings.supabase_storage_passport_bucket,
        storage_key,
        expires_in,
    )


def _sync_download(bucket: str, path: str) -> bytes:
    client = _get_client()
    return client.storage.from_(bucket).download(path)  # type: ignore[return-value]


async def download_source_document(bucket: str, path: str) -> bytes:
    """Download a source document from Supabase Storage and return raw bytes.

    Args:
        bucket: The Supabase Storage bucket name (e.g. "source-documents").
        path:   The object path within the bucket.
    Returns:
        Raw bytes of the stored file.
    Raises:
        Whatever the Supabase client raises on storage error.
    """
    return await asyncio.to_thread(_sync_download, bucket, path)


async def list_buckets() -> list[dict[str, object]]:
    """List all storage buckets — used for reachability checks."""
    return await asyncio.to_thread(_sync_list_buckets)


async def get_bucket_names() -> list[str]:
    """Return the names of all existing Storage buckets.

    Used by the health endpoint and startup verification to check that
    required buckets (source-documents, published-passports) exist before
    declaring the service fully operational.
    """
    return await asyncio.to_thread(_sync_get_bucket_names)
