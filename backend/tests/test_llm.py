"""LLM wrapper tests."""

from __future__ import annotations

import requests

from backend.llm.qwen_llm import QwenLLM


def test_safe_generate_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr("backend.llm.qwen_llm.settings.QWEN_API_KEY", None)
    monkeypatch.setattr("backend.llm.qwen_llm.settings.DASHSCOPE_API_KEY", None)
    llm = QwenLLM()
    response = llm.safe_generate_chat_completion([{"role": "user", "content": "你好"}])
    assert response is None


def test_qwen_prefers_dedicated_api_key(monkeypatch):
    monkeypatch.setattr("backend.llm.qwen_llm.settings.QWEN_API_KEY", "qwen-key")
    monkeypatch.setattr("backend.llm.qwen_llm.settings.DASHSCOPE_API_KEY", "fallback-key")
    llm = QwenLLM()
    assert llm.api_key == "qwen-key"


def test_request_failure_enters_cooldown(monkeypatch):
    monkeypatch.setattr("backend.llm.qwen_llm.settings.QWEN_API_KEY", "qwen-key")
    monkeypatch.setattr("backend.llm.qwen_llm.settings.DASHSCOPE_API_KEY", None)

    llm = QwenLLM()
    llm.__class__._cooldown_until = 0.0

    calls = {"count": 0}

    def failing_generate(*args, **kwargs):
      calls["count"] += 1
      raise requests.RequestException("network down")

    monkeypatch.setattr(llm, "generate_chat_completion", failing_generate)

    first = llm.safe_generate_chat_completion([{"role": "user", "content": "你好"}])
    second = llm.safe_generate_chat_completion([{"role": "user", "content": "再次请求"}])

    assert first is None
    assert second is None
    assert calls["count"] == 1

    llm.__class__._cooldown_until = 0.0
