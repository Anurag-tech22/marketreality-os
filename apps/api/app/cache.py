"""MarketReality OS – Simple in-memory TTL cache.

Avoids unnecessary CMC API calls for repeated requests within the TTL window.
"""

from __future__ import annotations

import time
from typing import Any


class SimpleCache:
    """Thread-safe in-memory cache with TTL expiration."""

    def __init__(self, ttl_seconds: int = 120):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self._ttl, value)

    def clear(self) -> None:
        self._store.clear()

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)
