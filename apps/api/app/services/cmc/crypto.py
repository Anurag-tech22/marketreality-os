"""CMC Cryptocurrency service — identity resolution, quotes, and info."""

from __future__ import annotations

from typing import Any

from .client import CMCClient


class CryptoService:
    """Handles cryptocurrency identity, quotes, and info lookups."""

    def __init__(self, client: CMCClient):
        self._client = client

    async def resolve_identity(self, symbol: str) -> dict:
        """Resolve a symbol to a CMC cryptocurrency map entry.

        Uses /v1/cryptocurrency/map to get the CMC ID, name, slug, rank,
        and active status for a given symbol.
        """
        data = await self._client.get(
            "/v1/cryptocurrency/map",
            {"symbol": symbol, "limit": 1},
        )
        items = data.get("data", [])
        if not items:
            return {}
        # Return the first (highest rank) match
        return items[0] if isinstance(items, list) else {}

    async def get_info(self, cmc_id: int) -> dict:
        """Get detailed cryptocurrency info by CMC ID.

        Uses /v2/cryptocurrency/info.
        """
        data = await self._client.get(
            "/v2/cryptocurrency/info",
            {"id": str(cmc_id)},
        )
        info_data = data.get("data", {})
        return info_data.get(str(cmc_id), {})

    async def get_quotes_latest(self, symbol: str) -> dict:
        """Get latest quote for a symbol.

        Uses /v2/cryptocurrency/quotes/latest.
        Returns the first match for the symbol.
        """
        data = await self._client.get(
            "/v2/cryptocurrency/quotes/latest",
            {"symbol": symbol, "convert": "USD"},
        )
        symbol_data = data.get("data", {}).get(symbol, [])
        if isinstance(symbol_data, list):
            return symbol_data[0] if symbol_data else {}
        return symbol_data or {}

    async def get_quotes_by_id(self, cmc_id: int) -> dict:
        """Get latest quote by CMC ID (more reliable than symbol lookup).

        Uses /v2/cryptocurrency/quotes/latest.
        """
        data = await self._client.get(
            "/v2/cryptocurrency/quotes/latest",
            {"id": str(cmc_id), "convert": "USD"},
        )
        return data.get("data", {}).get(str(cmc_id), {})
