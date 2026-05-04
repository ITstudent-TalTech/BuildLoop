import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.storage import list_buckets
from app.db.session import async_session_factory

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

VERSION = "0.1.0"

StatusValue = Literal["ok", "unavailable"]


async def _check_database() -> StatusValue:
    try:
        async with async_session_factory() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2.0)
        return "ok"
    except Exception as exc:
        logger.warning("Health DB check failed: %s", exc)
        return "unavailable"


async def _check_storage() -> StatusValue:
    try:
        await asyncio.wait_for(list_buckets(), timeout=2.0)
        return "ok"
    except Exception as exc:
        logger.warning("Health Storage check failed: %s", exc)
        return "unavailable"


@router.get("/health")
async def healthcheck(response: Response) -> dict[str, str]:
    """Return service health including database and storage status.

    Returns 200 with status=ok when all critical dependencies are healthy.
    Returns 503 when the database is unavailable (storage degradation is
    reported but does not trigger 503).
    """
    db_status, storage_status = await asyncio.gather(_check_database(), _check_storage())

    if db_status == "unavailable":
        response.status_code = 503

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "storage": storage_status,
        "version": VERSION,
    }
