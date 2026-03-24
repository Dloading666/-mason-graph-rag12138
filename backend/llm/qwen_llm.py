"""DashScope-compatible Qwen wrapper."""

from __future__ import annotations

import time
from typing import Any

import requests
from loguru import logger

from backend.config.settings import settings
from backend.llm.base_llm import BaseLLM


SAFE_TIMEOUT_CAP_SECONDS = 15
FAILURE_COOLDOWN_SECONDS = 300


class QwenLLM(BaseLLM):
    """Wrapper for DashScope OpenAI-compatible chat completions."""

    _cooldown_until = 0.0

    def __init__(self) -> None:
        self.api_key = settings.resolved_qwen_api_key
        self.base_url = settings.resolved_qwen_base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/chat/completions"
        self.model = settings.QWEN_MODEL
        self.temperature = settings.QWEN_TEMPERATURE
        self.max_tokens = settings.QWEN_MAX_TOKENS
        self.timeout = settings.QWEN_TIMEOUT_SECONDS

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise ValueError("Qwen API Key 未配置，请设置 QWEN_API_KEY 或 DASHSCOPE_API_KEY。")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _is_in_cooldown(self) -> bool:
        return time.time() < self.__class__._cooldown_until

    def _activate_cooldown(self, reason: str) -> None:
        self.__class__._cooldown_until = time.time() + FAILURE_COOLDOWN_SECONDS
        logger.warning(
            "Qwen temporarily disabled for {} seconds after {}. Falling back to local answer generation.",
            FAILURE_COOLDOWN_SECONDS,
            reason,
        )

    def generate_chat_completion(self, messages: list[dict[str, str]], *, timeout: int | None = None) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            json=payload,
            timeout=timeout or self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        choice = body.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        if not content:
            logger.error("Qwen completion returned an empty payload: {}", body)
            raise RuntimeError("Qwen completion returned an empty response.")
        return content.strip()

    def safe_generate_chat_completion(self, messages: list[dict[str, str]]) -> str | None:
        if not self.configured:
            logger.warning("Qwen API Key missing. Falling back to local answer generation.")
            return None

        if self._is_in_cooldown():
            logger.warning("Qwen is still in cooldown. Using local answer generation.")
            return None

        safe_timeout = min(self.timeout, SAFE_TIMEOUT_CAP_SECONDS) if self.timeout > 0 else SAFE_TIMEOUT_CAP_SECONDS
        try:
            return self.generate_chat_completion(messages, timeout=safe_timeout)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            logger.error("Qwen HTTP error: status={} body={}", status, getattr(exc.response, "text", ""))
            if status in {401, 403, 404, 429, 500, 502, 503, 504}:
                self._activate_cooldown(f"http-{status}")
            return None
        except requests.RequestException as exc:
            logger.error("Qwen request failed: {}", exc)
            self._activate_cooldown("request-exception")
            return None
        except RuntimeError as exc:
            logger.error("Qwen runtime failure: {}", exc)
            self._activate_cooldown("empty-response")
            return None
