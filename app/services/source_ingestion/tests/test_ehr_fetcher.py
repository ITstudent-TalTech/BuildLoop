"""Tests for EhrFetcher.

All tests mock httpx at the AsyncClient level — no real network calls.
The sample_ehr.pdf fixture is the canonical mock response body.

Acceptance criteria covered:
  - Successful fetch computes checksum and returns ok=True.
  - HTTP 404 from EHR returns ok=False with status_code=404.
  - HTTP 500 from EHR returns ok=False with status_code=500.
  - SSLError triggers SSL fallback and sets ssl_fallback_used=True.
  - SSLError with fallback disabled returns ok=False without retrying.
  - Checksum is SHA-256 hex of the response bytes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.source_ingestion.ehr_fetcher import EhrFetcher

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_ehr.pdf"
SAMPLE_BYTES = FIXTURE_PDF.read_bytes()
SAMPLE_CHECKSUM = hashlib.sha256(SAMPLE_BYTES).hexdigest()


def _make_response(status_code: int, content: bytes = b"") -> httpx.Response:
    """Build a minimal httpx.Response for mocking."""
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={"content-type": "application/pdf"},
    )


def _patch_client(responses: list[httpx.Response]) -> tuple:
    """Return (patcher, mock_client) where client.get returns responses in order."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=responses)

    # httpx.AsyncClient is used as a context manager: async with ... as client
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    patcher = patch("app.services.source_ingestion.ehr_fetcher.httpx.AsyncClient", return_value=mock_ctx)
    return patcher, mock_client


# ---------------------------------------------------------------------------
# Successful fetch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_pdf_success_returns_ok() -> None:
    """200 OK with PDF bytes → ok=True, content matches fixture, ssl_fallback_used=False."""
    patcher, _ = _patch_client([_make_response(200, SAMPLE_BYTES)])
    with patcher:
        fetcher = EhrFetcher()
        result = await fetcher.fetch_pdf("101035685")

    assert result.ok is True
    assert result.content == SAMPLE_BYTES
    assert result.ssl_fallback_used is False
    assert result.status_code == 200
    assert result.error is None


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_pdf_checksum_is_sha256_hex() -> None:
    """Checksum on a successful fetch is SHA-256 hex of response bytes."""
    patcher, _ = _patch_client([_make_response(200, SAMPLE_BYTES)])
    with patcher:
        fetcher = EhrFetcher()
        result = await fetcher.fetch_pdf("101035685")

    assert result.checksum == SAMPLE_CHECKSUM


# ---------------------------------------------------------------------------
# HTTP error codes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_pdf_404_returns_not_ok() -> None:
    """HTTP 404 from EHR → ok=False, status_code=404, no content."""
    patcher, _ = _patch_client([_make_response(404)])
    with patcher:
        fetcher = EhrFetcher()
        result = await fetcher.fetch_pdf("101035685")

    assert result.ok is False
    assert result.status_code == 404
    assert result.content is None
    assert "ehr_http_404" in (result.error or "")


@pytest.mark.asyncio
async def test_fetch_pdf_500_returns_not_ok() -> None:
    """HTTP 500 from EHR → ok=False, status_code=500, error captured."""
    patcher, _ = _patch_client([_make_response(500)])
    with patcher:
        fetcher = EhrFetcher()
        result = await fetcher.fetch_pdf("101035685")

    assert result.ok is False
    assert result.status_code == 500
    assert result.content is None
    assert "ehr_http_500" in (result.error or "")


# ---------------------------------------------------------------------------
# SSL fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_pdf_ssl_error_triggers_fallback() -> None:
    """SSLError on first attempt → retry without verification → ok=True, ssl_fallback_used=True."""
    ssl_exc = httpx.ConnectError("SSL handshake failed")

    mock_fallback_client = AsyncMock()
    mock_fallback_client.get = AsyncMock(return_value=_make_response(200, SAMPLE_BYTES))
    mock_fallback_ctx = AsyncMock()
    mock_fallback_ctx.__aenter__ = AsyncMock(return_value=mock_fallback_client)
    mock_fallback_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_first_client = AsyncMock()
    mock_first_client.get = AsyncMock(side_effect=ssl_exc)
    mock_first_ctx = AsyncMock()
    mock_first_ctx.__aenter__ = AsyncMock(return_value=mock_first_client)
    mock_first_ctx.__aexit__ = AsyncMock(return_value=False)

    call_count = 0

    def _client_factory(**kwargs: object) -> object:
        nonlocal call_count
        call_count += 1
        return mock_first_ctx if call_count == 1 else mock_fallback_ctx

    with patch("app.services.source_ingestion.ehr_fetcher.httpx.AsyncClient", side_effect=_client_factory):
        fetcher = EhrFetcher()
        result = await fetcher.fetch_pdf("101035685")

    assert result.ok is True
    assert result.ssl_fallback_used is True
    assert result.content == SAMPLE_BYTES
    assert "warning" in result.fetch_metadata
    assert "retried_without_tls" in result.fetch_metadata["warning"]


@pytest.mark.asyncio
async def test_fetch_pdf_ssl_error_fallback_disabled_returns_failure() -> None:
    """SSLError with INGEST_EHR_SSL_FALLBACK=False → ok=False, no retry."""
    ssl_exc = httpx.ConnectError("SSL handshake failed")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ssl_exc)
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.source_ingestion.ehr_fetcher.httpx.AsyncClient", return_value=mock_ctx):
        fetcher = EhrFetcher()
        fetcher._ssl_fallback = False  # disable fallback
        result = await fetcher.fetch_pdf("101035685")

    assert result.ok is False
    assert result.ssl_fallback_used is False
    assert "ssl_error" in (result.error or "")
    assert mock_client.get.call_count == 1  # only one attempt


# ---------------------------------------------------------------------------
# Source URI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_pdf_source_uri_contains_ehr_code() -> None:
    """source_uri must embed the ehr_code and the expected URL path."""
    patcher, _ = _patch_client([_make_response(200, SAMPLE_BYTES)])
    with patcher:
        fetcher = EhrFetcher()
        result = await fetcher.fetch_pdf("101035685")

    assert "101035685" in result.source_uri
    assert "pdf/document/file" in result.source_uri
