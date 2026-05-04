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

    # Accept both 200 (all ok) and 503 (db unavailable in test env)
    assert response.status_code in (200, 503)

    body = response.json()
    assert "status" in body
    assert body["status"] in ("ok", "degraded")
    assert "database" in body
    assert body["database"] in ("ok", "unavailable")
    assert "storage" in body
    assert body["storage"] in ("ok", "unavailable")
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
