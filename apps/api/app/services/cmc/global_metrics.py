"""CMC Global Metrics service — market-wide context."""

from __future__ import annotations

from .client import CMCClient


class GlobalMetricsService:
    """Fetches global market context from CMC."""

    def __init__(self, client: CMCClient):
        self._client = client

    async def get_latest(self) -> dict:
        """Get latest global market metrics.

        Uses /v1/global-metrics/quotes/latest.
        """
        data = await self._client.get(
            "/v1/global-metrics/quotes/latest",
            {"convert": "USD"},
        )
        return data.get("data", {})
