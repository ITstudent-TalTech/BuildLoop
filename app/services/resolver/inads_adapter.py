"""HTTP adapter for the Estonian In-ADS (inaadress.maaamet.ee) gazetteer API.

Wraps httpx.AsyncClient. The request shape, query parameters, headers, timeout,
and error-handling semantics are lifted directly from resolve_address_to_ehr()
in buildloop_passport_from_address.py (lines 260–283).

SSL fallback: the script uses requests.Session(verify=False) as a fallback after
SSLError. This adapter preserves that behaviour behind RESOLVER_INADS_SSL_FALLBACK
(default True) — a known workaround for Estonian network paths with incomplete
cert chains. Disable in environments that have correct PKI.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.resolver.types import InAdsResponse

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "BuildLoop-Passport-From-Address/1.0",
    "Accept": "*/*",
}


def _is_ssl_related(exc: BaseException) -> bool:
    """Heuristic: decide whether an httpx exception is SSL/TLS in origin."""
    msg = str(exc).lower()
    return any(kw in msg for kw in ("ssl", "certificate", "tls", "handshake"))


class InAdsAdapter:
    """Async HTTP client for the In-ADS gazetteer endpoint.

    Instantiate once per request (or inject a mock in tests).
    Settings are read lazily to avoid triggering get_settings() at import time.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.resolver_inads_base_url.rstrip("/")
        self._features = settings.resolver_inads_features
        self._ssl_fallback = settings.resolver_inads_ssl_fallback

    async def search(
        self,
        query: str,
        features: str | None = None,
    ) -> InAdsResponse:
        """Query the In-ADS gazetteer for address candidates.

        Inputs:  query string (raw address variant), optional feature override.
        Outputs: InAdsResponse — never raises; errors captured in .error field.

        Mirrors the script's query URL:
          {base}/gazetteer?results=10&features=...&address=...&seosreg=1&ehr1=1&ehr2=1
        with timeout=60 and the same User-Agent header.

        On SSLError (if RESOLVER_INADS_SSL_FALLBACK is True): retries once
        without certificate verification, recording ssl_fallback_used=True.
        """
        params: dict[str, Any] = {
            "results": "10",
            "features": features or self._features,
            "address": query,
            "seosreg": "1",
            "ehr1": "1",
            "ehr2": "1",
        }
        url = f"{self._base_url}/gazetteer"
        ssl_error_msg: str | None = None

        # --- First attempt: SSL verification enabled ---
        try:
            async with httpx.AsyncClient(verify=True) as client:
                resp = await client.get(
                    url, params=params, headers=_DEFAULT_HEADERS, timeout=60.0
                )
            return self._parse_response(resp, ssl_fallback_used=False)
        except Exception as exc:
            if _is_ssl_related(exc):
                ssl_error_msg = f"{type(exc).__name__}: {exc}"
            else:
                return InAdsResponse(
                    ok=False,
                    data=None,
                    error=f"resolver_network_error: {type(exc).__name__}: {exc}",
                )

        # --- SSL fallback: retry without certificate verification ---
        if not self._ssl_fallback:
            return InAdsResponse(
                ok=False,
                data=None,
                error=f"resolver_ssl_error: {ssl_error_msg}",
            )

        logger.warning(
            "In-ADS SSL verification failed; retrying without verification. "
            "Set RESOLVER_INADS_SSL_FALLBACK=false to disable. Error: %s",
            ssl_error_msg,
        )
        try:
            async with httpx.AsyncClient(verify=False) as client:  # noqa: S501
                resp = await client.get(
                    url, params=params, headers=_DEFAULT_HEADERS, timeout=60.0
                )
            return self._parse_response(resp, ssl_fallback_used=True)
        except Exception as exc:
            return InAdsResponse(
                ok=False,
                data=None,
                ssl_fallback_used=True,
                error=f"resolver_network_error: {type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _parse_response(
        resp: httpx.Response, *, ssl_fallback_used: bool
    ) -> InAdsResponse:
        logger.warning("INADS DEBUG: status=%s body=%s", resp.status_code, resp.text[:2000])
        if resp.status_code != 200:
            return InAdsResponse(
                ok=False,
                data=None,
                ssl_fallback_used=ssl_fallback_used,
                error=f"resolver_http_{resp.status_code}",
                status_code=resp.status_code,
            )
        try:
            data = resp.json()
        except Exception:
            return InAdsResponse(
                ok=False,
                data=None,
                ssl_fallback_used=ssl_fallback_used,
                error="resolver_non_json_body",
                status_code=resp.status_code,
            )
        return InAdsResponse(
            ok=True,
            data=data,
            ssl_fallback_used=ssl_fallback_used,
            status_code=resp.status_code,
        )
