"""Async HTTP adapter for the Estonian EHR PDF endpoint.

Wraps httpx.AsyncClient. The request shape, headers, timeout, and SSL-fallback
semantics are lifted directly from fetch_pdf() in buildloop_passport_from_address.py
(lines 340-399).

URL pattern: {EHR_BASE_URL}/pdf/document/file/{ehr_code}
  Verified against the script (line 341). The task description suggested a
  different path ({ehr_code}/file) but the script is the source of truth.

SSL fallback: on SSLError, retry once without certificate verification,
  gated by INGEST_EHR_SSL_FALLBACK (default True). Mirrors inads_adapter.py.

Checksum: SHA-256 hex of response bytes, computed here so the service layer
  doesn't need to import hashlib.

TODO(2.3 review): Script uses timeout=90; the ingest_ehr_timeout_seconds setting
  defaults to 60 per the session spec. Verify with EHR operator whether 60s is
  sufficient before switching to production. If long PDFs require 90s, bump the
  default or configure per-environment.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.source_ingestion.types import EhrFetchResult

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS: dict[str, str] = {
    "Accept": "application/pdf",
}


def _is_ssl_related(exc: BaseException) -> bool:
    """Heuristic: decide whether an httpx exception is SSL/TLS in origin."""
    msg = str(exc).lower()
    return any(kw in msg for kw in ("ssl", "certificate", "tls", "handshake"))


class EhrFetcher:
    """Async HTTP client for the EHR PDF endpoint.

    Instantiate once per request (or inject a mock in tests).
    Settings are read lazily to avoid triggering get_settings() at import time.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.ingest_ehr_base_url.rstrip("/")
        self._timeout = float(settings.ingest_ehr_timeout_seconds)
        self._ssl_fallback = settings.ingest_ehr_ssl_fallback

    async def fetch_pdf(self, ehr_code: str) -> EhrFetchResult:
        """Fetch an EHR PDF by building code.

        Inputs:  ehr_code — the Estonian EHR building identifier.
        Outputs: EhrFetchResult — never raises; errors captured in .error / .ok.

        URL: {EHR_BASE_URL}/pdf/document/file/{ehr_code}
        On SSLError (if INGEST_EHR_SSL_FALLBACK is True): retries once
        without certificate verification, recording ssl_fallback_used=True.
        On success: checksum (SHA-256 hex) is computed from the response bytes.
        """
        url = f"{self._base_url}/pdf/document/file/{ehr_code}"
        ssl_error_msg: str | None = None

        # --- First attempt: SSL verification enabled ---
        try:
            async with httpx.AsyncClient(verify=True) as client:
                resp = await client.get(
                    url, headers=_DEFAULT_HEADERS, timeout=self._timeout
                )
            return self._parse_response(resp, url, ssl_fallback_used=False)
        except Exception as exc:
            if _is_ssl_related(exc):
                ssl_error_msg = f"{type(exc).__name__}: {exc}"
            else:
                return EhrFetchResult(
                    ok=False,
                    content=None,
                    checksum=None,
                    source_uri=url,
                    error=f"ehr_network_error: {type(exc).__name__}: {exc}",
                    ssl_fallback_used=False,
                    status_code=None,
                    fetch_metadata={"url": url, "ssl_verify": True},
                )

        # --- SSL fallback: retry without certificate verification ---
        if not self._ssl_fallback:
            return EhrFetchResult(
                ok=False,
                content=None,
                checksum=None,
                source_uri=url,
                error=f"ehr_ssl_error: {ssl_error_msg}",
                ssl_fallback_used=False,
                status_code=None,
                fetch_metadata={"url": url, "ssl_verify": True},
            )

        logger.warning(
            "EHR SSL verification failed; retrying without verification. "
            "Set INGEST_EHR_SSL_FALLBACK=false to disable. Error: %s",
            ssl_error_msg,
        )
        try:
            async with httpx.AsyncClient(verify=False) as client:  # noqa: S501
                resp = await client.get(
                    url, headers=_DEFAULT_HEADERS, timeout=self._timeout
                )
            result = self._parse_response(resp, url, ssl_fallback_used=True)
            # Attach the SSL warning from the first attempt into fetch_metadata
            result.fetch_metadata["warning"] = (
                f"retried_without_tls_verification_after_ssl_error: {ssl_error_msg}"
            )
            return result
        except Exception as exc:
            return EhrFetchResult(
                ok=False,
                content=None,
                checksum=None,
                source_uri=url,
                error=f"ehr_network_error: {type(exc).__name__}: {exc}",
                ssl_fallback_used=True,
                status_code=None,
                fetch_metadata={
                    "url": url,
                    "ssl_verify": False,
                    "warning": f"initial_ssl_error: {ssl_error_msg}",
                },
            )

    @staticmethod
    def _parse_response(
        resp: httpx.Response,
        url: str,
        *,
        ssl_fallback_used: bool,
    ) -> EhrFetchResult:
        metadata: dict[str, Any] = {
            "url": url,
            "http_code": resp.status_code,
            "content_type": resp.headers.get("content-type", ""),
            "ssl_verify": not ssl_fallback_used,
        }

        if resp.status_code == 200:
            content = resp.content
            # Only accept non-empty responses
            if not content:
                return EhrFetchResult(
                    ok=False,
                    content=None,
                    checksum=None,
                    source_uri=url,
                    error="ehr_empty_response",
                    ssl_fallback_used=ssl_fallback_used,
                    status_code=200,
                    fetch_metadata={**metadata, "bytes": 0},
                )
            checksum = hashlib.sha256(content).hexdigest()
            return EhrFetchResult(
                ok=True,
                content=content,
                checksum=checksum,
                source_uri=url,
                error=None,
                ssl_fallback_used=ssl_fallback_used,
                status_code=200,
                fetch_metadata={**metadata, "bytes": len(content)},
            )

        # Non-200 response
        preview = resp.text[:1000] if resp.content else ""
        return EhrFetchResult(
            ok=False,
            content=None,
            checksum=None,
            source_uri=url,
            error=f"ehr_http_{resp.status_code}",
            ssl_fallback_used=ssl_fallback_used,
            status_code=resp.status_code,
            fetch_metadata={**metadata, "response_preview": preview},
        )
