"""CMC Historical service — historical quotes and OHLCV data."""

from __future__ import annotations

from typing import Any

from .client import CMCClient


class HistoricalService:
    """Fetches historical market data from CMC."""

    def __init__(self, client: CMCClient):
        self._client = client

    async def get_quotes_historical(
        self,
        cmc_id: int | None = None,
        symbol: str | None = None,
        time_start: str | None = None,
        time_end: str | None = None,
        count: int = 10,
        interval: str = "daily",
    ) -> dict:
        """Get historical quotes.

        Uses /v3/cryptocurrency/quotes/historical.
        """
        params: dict[str, Any] = {
            "convert": "USD",
            "count": count,
            "interval": interval,
        }
        if cmc_id is not None:
            params["id"] = str(cmc_id)
        elif symbol:
            params["symbol"] = symbol
        else:
            raise ValueError("Either cmc_id or symbol is required")

        if time_start:
            params["time_start"] = time_start
        if time_end:
            params["time_end"] = time_end

        data = await self._client.get(
            "/v3/cryptocurrency/quotes/historical",
            params,
        )
        return data.get("data", {})

    async def get_ohlcv_historical(
        self,
        cmc_id: int | None = None,
        symbol: str | None = None,
        time_start: str | None = None,
        time_end: str | None = None,
        count: int = 10,
        time_period: str = "daily",
    ) -> dict:
        """Get historical OHLCV data.

        Uses /v2/cryptocurrency/ohlcv/historical.
        """
        params: dict[str, Any] = {
            "convert": "USD",
            "count": count,
            "time_period": time_period,
        }
        if cmc_id is not None:
            params["id"] = str(cmc_id)
        elif symbol:
            params["symbol"] = symbol
        else:
            raise ValueError("Either cmc_id or symbol is required")

        if time_start:
            params["time_start"] = time_start
        if time_end:
            params["time_end"] = time_end

        data = await self._client.get(
            "/v2/cryptocurrency/ohlcv/historical",
            params,
        )
        return data.get("data", {})
