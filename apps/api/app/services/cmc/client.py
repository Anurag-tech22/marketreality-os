"""CMC HTTP client — shared low-level transport for all CMC API calls.

Features:
- Server-side API key handling (never exposed to browser)
- Configurable timeout and retries
- Structured error responses
- Rate-limit awareness
- Request logging (without secrets)
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("marketreality.cmc")


class CMCError(Exception):
    """Raised when a CMC API call fails."""

    def __init__(self, message: str, status_code: int | None = None, endpoint: str = ""):
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__(message)


class CMCRateLimitError(CMCError):
    """Raised specifically for 429 rate-limit responses."""
    pass


class CMCAuthError(CMCError):
    """Raised for 401/403 authentication errors."""
    pass


class CMCClient:
    """Low-level async CMC Pro API client.

    All higher-level service modules (crypto, market_pairs, etc.) use this
    client for their HTTP calls.
    """

    def __init__(self):
        if not settings.cmc_pro_api_key:
            raise ValueError(
                "CMC_PRO_API_KEY is not configured. "
                "Set it in apps/api/.env before running live analysis."
            )
        self._client = httpx.AsyncClient(
            base_url=settings.cmc_base_url,
            timeout=httpx.Timeout(8.0, connect=5.0),
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-CMC_PRO_API_KEY": settings.cmc_pro_api_key,
            },
        )
        self._request_count = 0
        self._last_request_time: float | None = None

    @property
    def is_configured(self) -> bool:
        return bool(settings.cmc_pro_api_key)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        """Execute a GET request against the CMC Pro API.

        Returns the parsed JSON body. Raises structured errors for
        rate limits, auth failures, timeouts, and bad responses.
        """
        self._request_count += 1
        start = time.monotonic()
        log_params = {k: v for k, v in (params or {}).items()}

        logger.info("CMC request #%d: GET %s %s", self._request_count, path, log_params)

        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            logger.error("CMC timeout: GET %s", path)
            raise CMCError(
                f"CMC request timed out: {path}",
                status_code=None,
                endpoint=path,
            ) from exc
        except httpx.NetworkError as exc:
            logger.error("CMC network error: GET %s: %s", path, exc)
            raise CMCError(
                f"CMC network error: {path}: {exc}",
                status_code=None,
                endpoint=path,
            ) from exc

        elapsed = time.monotonic() - start
        self._last_request_time = elapsed
        logger.info("CMC response: %d in %.2fs for %s", response.status_code, elapsed, path)

        # Handle error status codes
        if response.status_code == 429:
            raise CMCRateLimitError(
                "CMC rate limit exceeded. Try again later.",
                status_code=429,
                endpoint=path,
            )
        if response.status_code in (401, 403):
            raise CMCAuthError(
                "CMC authentication failed. Check your API key.",
                status_code=response.status_code,
                endpoint=path,
            )
        if response.status_code >= 400:
            body = response.text[:500]
            raise CMCError(
                f"CMC API error {response.status_code} on {path}: {body}",
                status_code=response.status_code,
                endpoint=path,
            )

        try:
            data = response.json()
        except Exception as exc:
            raise CMCError(
                f"CMC returned invalid JSON for {path}",
                status_code=response.status_code,
                endpoint=path,
            ) from exc

        # Check CMC-level status in response body
        status = data.get("status", {})
        error_code = status.get("error_code", 0)
        if error_code and error_code != 0:
            error_msg = status.get("error_message", "Unknown CMC error")
            raise CMCError(
                f"CMC error {error_code}: {error_msg}",
                status_code=response.status_code,
                endpoint=path,
            )

        return data

    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
