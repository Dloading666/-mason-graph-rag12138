"""Agent abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Minimal interface for future multi-agent orchestration."""

    @abstractmethod
    def run(self, question: str) -> dict:
        raise NotImplementedError

