"""CMC Market Pairs service — pair discovery and venue analysis."""

from __future__ import annotations

from typing import Any

from .client import CMCClient


class MarketPairsService:
    """Discovers and normalizes market pairs for a cryptocurrency."""

    def __init__(self, client: CMCClient):
        self._client = client

    async def get_market_pairs(
        self,
        cmc_id: int | None = None,
        symbol: str | None = None,
        limit: int = 500,
        category: str | None = None,
    ) -> dict:
        """Get market pairs for a cryptocurrency.

        Uses /v2/cryptocurrency/market-pairs/latest.
        Prefers cmc_id over symbol for accuracy.
        """
        params: dict[str, Any] = {
            "convert": "USD",
            "limit": limit,
        }
        if cmc_id is not None:
            params["id"] = str(cmc_id)
        elif symbol:
            params["symbol"] = symbol
        else:
            raise ValueError("Either cmc_id or symbol is required")

        if category:
            params["category"] = category

        data = await self._client.get(
            "/v2/cryptocurrency/market-pairs/latest",
            params,
        )
        return data.get("data", {})

    async def get_exchange_pairs(
        self,
        exchange_id: int | None = None,
        exchange_slug: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Get market pairs for a specific exchange.

        Uses /v1/exchange/market-pairs/latest.
        """
        params: dict[str, Any] = {
            "convert": "USD",
            "limit": limit,
        }
        if exchange_id is not None:
            params["id"] = str(exchange_id)
        elif exchange_slug:
            params["slug"] = exchange_slug
        else:
            raise ValueError("Either exchange_id or exchange_slug is required")

        data = await self._client.get(
            "/v1/exchange/market-pairs/latest",
            params,
        )
        return data.get("data", {})
