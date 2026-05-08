import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.health import router as health_router
from app.api.routes.intakes import router as intakes_router
from app.api.routes.resolutions import router as resolutions_router
from app.api.routes.sources import router as sources_router
from app.core.config import get_settings
from app.core.storage import get_bucket_names
from app.db.session import async_session_factory, engine

logger = logging.getLogger(__name__)

VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    # Startup: verify DB connectivity
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connectivity OK")
    except Exception as exc:
        logger.error("Database connectivity FAILED at startup: %s", exc)

    # Startup: verify Supabase Storage reachability and required bucket presence
    try:
        names = await asyncio.wait_for(get_bucket_names(), timeout=5.0)
        required = {
            settings.supabase_storage_source_bucket,
            settings.supabase_storage_passport_bucket,
        }
        missing = sorted(required - set(names))
        if missing:
            missing_list = "\n".join(f"  - {b}" for b in missing)
            logger.warning(
                "[STARTUP WARNING] Required Supabase Storage buckets are missing:\n%s\n"
                "Create them in the Supabase dashboard before fetching source documents.\n"
                "Doc: https://supabase.com/docs/guides/storage/buckets/creating-buckets",
                missing_list,
            )
        else:
            logger.info("Supabase Storage OK — both required buckets verified")
    except Exception as exc:
        logger.warning("Supabase Storage unreachable at startup (non-fatal): %s", exc)

    yield

    # Shutdown: dispose engine
    await engine.dispose()
    logger.info("Database engine disposed")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="BUILDLoop Passport Engine",
        version=VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/v1")
    app.include_router(intakes_router, prefix="/v1")
    app.include_router(resolutions_router, prefix="/v1")
    app.include_router(sources_router, prefix="/v1")

    return app


app = create_app()
