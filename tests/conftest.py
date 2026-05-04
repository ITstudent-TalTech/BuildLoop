"""Test suite configuration.

IMPORTANT — isolation contract:
  Tests NEVER run against the real Supabase.
  All DB tests require a separate Postgres instance declared via
  DATABASE_URL_TEST.  If the variable is unset, the session fails
  immediately with a clear error so the developer doesn't accidentally
  hit production.
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Fail fast — do not let tests silently run against real Supabase
_TEST_DB_URL = os.environ.get("DATABASE_URL_TEST")
if _TEST_DB_URL is None:
    raise RuntimeError(
        "DATABASE_URL_TEST is not set. "
        "Set it to a dedicated test Postgres URL before running the test suite. "
        "Tests must never run against the real Supabase database."
    )


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncSession:
    """Async DB session that rolls back after each test.

    Each test gets a fresh transaction that is rolled back on teardown —
    no test data persists to the next test, and no cleanup helpers are
    required.
    """
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        async with factory(bind=conn) as session:
            yield session
            await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncClient:
    """httpx AsyncClient targeting the FastAPI app.

    The Supabase storage check is expected to fail (no real credentials
    in the test environment); this is acceptable — the health endpoint
    reports it as 'unavailable' rather than crashing.
    """
    # Patch settings before importing app to avoid ValidationError on
    # missing env vars in CI.  Tests that need real Settings should set
    # the variables themselves.
    os.environ.setdefault("DATABASE_URL", _TEST_DB_URL)
    os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

    # Import app after env vars are set
    from app.main import app  # noqa: PLC0415

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
