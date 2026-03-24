"""In-memory TTL cache for frequently asked questions."""

from __future__ import annotations

import time

from backend.cache.base_cache import BaseCache


class MasonCache(BaseCache):
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, object]] = {}

    def get(self, key: str):
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value, ttl_seconds: int = 600) -> None:
        self._store[key] = (time.time() + ttl_seconds, value)

