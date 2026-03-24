"""Cache abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseCache(ABC):
    @abstractmethod
    def get(self, key: str):
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value, ttl_seconds: int = 600) -> None:
        raise NotImplementedError

