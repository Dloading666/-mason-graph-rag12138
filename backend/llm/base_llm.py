"""LLM abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Minimal interface for chat-completion style models."""

    @abstractmethod
    def generate_chat_completion(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

