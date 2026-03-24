"""Embedding wrapper tests."""

from __future__ import annotations

from backend.embedding.ali_embedding import AliTextEmbedding


def test_embed_empty_text_returns_none():
    embedder = AliTextEmbedding()
    assert embedder.safe_embed_text("   ") is None


def test_embedding_prefers_dedicated_api_key(monkeypatch):
    monkeypatch.setattr("backend.embedding.ali_embedding.settings.EMBEDDING_API_KEY", "embedding-key")
    monkeypatch.setattr("backend.embedding.ali_embedding.settings.DASHSCOPE_API_KEY", "fallback-key")
    embedder = AliTextEmbedding()
    assert embedder.api_key == "embedding-key"
