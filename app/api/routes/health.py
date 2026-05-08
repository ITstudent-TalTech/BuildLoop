import asyncio
import logging
from typing import Any, Literal

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.config import get_settings
from app.core.storage import get_bucket_names
from app.db.session import async_session_factory

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

VERSION = "0.1.0"

DbStatus = Literal["ok", "unavailable"]
StorageStatus = Literal["ok", "missing_buckets", "unavailable"]


async def _check_database() -> DbStatus:
    try:
        async with async_session_factory() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2.0)
        return "ok"
    except Exception as exc:
        logger.warning("Health DB check failed: %s", exc)
        return "unavailable"


async def _check_storage() -> tuple[StorageStatus, list[str]]:
    """Verify Supabase Storage is reachable and both required buckets exist.

    Returns:
      ("ok", [])                     — both buckets present and reachable.
      ("missing_buckets", [...])     — reachable but one or more buckets absent.
      ("unavailable", [])            — Supabase unreachable or call timed out.
    """
    settings = get_settings()
    required = {
        settings.supabase_storage_source_bucket,
        settings.supabase_storage_passport_bucket,
    }
    try:
        names = await asyncio.wait_for(get_bucket_names(), timeout=2.0)
        missing = sorted(required - set(names))
        if missing:
            logger.warning(
                "Health Storage check: required buckets missing: %s", missing
            )
            return "missing_buckets", missing
        return "ok", []
    except Exception as exc:
        logger.warning("Health Storage check failed: %s", exc)
        return "unavailable", []


@router.get("/health")
async def healthcheck(response: Response) -> dict[str, Any]:
    """Return service health including database and storage bucket status.

    Returns 200 when all critical dependencies are healthy, or when buckets
    are missing (configuration problem, not a system failure).
    Returns 503 when the database or Supabase Storage itself is unreachable.

    Response shape:
      {
        "status": "ok" | "degraded",
        "database": "ok" | "unavailable",
        "storage": "ok" | "missing_buckets" | "unavailable",
        "missing_buckets": ["bucket-name", ...],   # only when storage=missing_buckets
        "version": "x.y.z"
      }
    """
    results = await asyncio.gather(_check_database(), _check_storage())
    db_status: DbStatus = results[0]  # type: ignore[assignment]
    storage_status: StorageStatus
    missing_buckets: list[str]
    storage_status, missing_buckets = results[1]  # type: ignore[misc]

    if db_status == "unavailable" or storage_status == "unavailable":
        response.status_code = 503

    body: dict[str, Any] = {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "storage": storage_status,
        "version": VERSION,
    }
    if missing_buckets:
        body["missing_buckets"] = missing_buckets
    return body
