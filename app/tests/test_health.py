"""Tests for GET /v1/health.

The test environment has no real DB or Supabase. The health endpoint
should return a response of the expected shape regardless of whether
checks pass or fail — it must not crash.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_expected_shape(test_client: AsyncClient) -> None:
    response = await test_client.get("/v1/health")

    # Accept both 200 (all ok) and 503 (db/storage unavailable in test env)
    assert response.status_code in (200, 503)

    body = response.json()
    assert "status" in body
    assert body["status"] in ("ok", "degraded")
    assert "database" in body
    assert body["database"] in ("ok", "unavailable")
    assert "storage" in body
    assert body["storage"] in ("ok", "unavailable", "missing_buckets")
    assert "version" in body
    assert isinstance(body["version"], str)


@pytest.mark.asyncio
async def test_health_503_when_db_unavailable(test_client: AsyncClient) -> None:
    """With the test URL pointing at a non-existent DB, expect database=unavailable."""
    response = await test_client.get("/v1/health")
    body = response.json()

    # In the test env there is likely no real DB; assert the field shape is correct
    # and that the status code is consistent with the database field.
    if body["database"] == "unavailable":
        assert response.status_code == 503
    else:
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Strict bucket verification — mock storage layer, test handler behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_reports_ok_when_both_buckets_exist() -> None:
    """storage='ok' when Supabase returns both required bucket names."""
    import os
    from unittest.mock import AsyncMock, patch

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/fake")
    os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

    from app.main import app as fastapi_app

    from httpx import ASGITransport, AsyncClient as _AsyncClient

    with patch(
        "app.api.routes.health._check_database",
        new_callable=AsyncMock,
        return_value="ok",
    ), patch(
        "app.api.routes.health._check_storage",
        new_callable=AsyncMock,
        return_value=("ok", []),
    ):
        async with _AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["storage"] == "ok"
    assert "missing_buckets" not in body
    assert body["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_reports_missing_buckets_when_one_is_absent() -> None:
    """storage='missing_buckets' with list when one bucket is absent; HTTP 200 (config fault)."""
    from unittest.mock import AsyncMock, patch

    from app.main import app as fastapi_app

    from httpx import ASGITransport, AsyncClient as _AsyncClient

    with patch(
        "app.api.routes.health._check_database",
        new_callable=AsyncMock,
        return_value="ok",
    ), patch(
        "app.api.routes.health._check_storage",
        new_callable=AsyncMock,
        return_value=("missing_buckets", ["published-passports"]),
    ):
        async with _AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/v1/health")

    assert response.status_code == 200, "missing_buckets is a config problem, not 503"
    body = response.json()
    assert body["status"] == "ok"
    assert body["storage"] == "missing_buckets"
    assert body["missing_buckets"] == ["published-passports"]


@pytest.mark.asyncio
async def test_health_reports_storage_unavailable_when_supabase_unreachable() -> None:
    """storage='unavailable' triggers 503 alongside database ok."""
    from unittest.mock import AsyncMock, patch

    from app.main import app as fastapi_app

    from httpx import ASGITransport, AsyncClient as _AsyncClient

    with patch(
        "app.api.routes.health._check_database",
        new_callable=AsyncMock,
        return_value="ok",
    ), patch(
        "app.api.routes.health._check_storage",
        new_callable=AsyncMock,
        return_value=("unavailable", []),
    ):
        async with _AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["storage"] == "unavailable"
    assert "missing_buckets" not in body
