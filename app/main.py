import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.storage import list_buckets
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

    # Startup: verify Supabase reachability (non-fatal)
    try:
        import asyncio
        await asyncio.wait_for(list_buckets(), timeout=5.0)
        logger.info("Supabase Storage reachability OK")
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

    return app


app = create_app()
