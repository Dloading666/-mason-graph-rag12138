"""DashScope-compatible embedding wrapper."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import requests
from loguru import logger

from backend.config.settings import settings
from backend.embedding.base_embedding import BaseEmbedding


class AliTextEmbedding(BaseEmbedding):
    """Wrapper for DashScope OpenAI-compatible embeddings."""

    def __init__(self) -> None:
        self.api_key = settings.resolved_embedding_api_key
        self.base_url = settings.resolved_embedding_base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/embeddings"
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.timeout = settings.EMBEDDING_TIMEOUT_SECONDS
        self._disabled = False

    @property
    def configured(self) -> bool:
        return bool(self.api_key) and not self._disabled

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise ValueError("Embedding API Key 未配置或已降级为仅关键词检索。")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def embed_text(self, text: str, *, text_type: str = "document") -> np.ndarray | None:
        text = text.strip()
        if not text:
            logger.warning("Skip empty text embedding request.")
            return None
        if not self.configured:
            logger.warning("Embedding unavailable. Retrieval will fall back to keyword mode.")
            return None

        payload = {
            "model": self.model,
            "input": text,
            "dimensions": self.dimension,
        }
        response = requests.post(
            self.endpoint,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data", [])
        if not data:
            logger.error("Embedding response missing data: {}", body)
            return None
        return np.asarray(data[0]["embedding"], dtype=np.float32)

    def safe_embed_text(self, text: str, *, text_type: str = "document") -> np.ndarray | None:
        if self._disabled:
            return None
        try:
            return self.embed_text(text, text_type=text_type)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            logger.error("Embedding HTTP error: status={} body={}", status, getattr(exc.response, "text", ""))
            if status in {401, 403, 404, 429}:
                self._disabled = True
            return None
        except requests.RequestException as exc:
            logger.error("Embedding request failed: {}", exc)
            self._disabled = True
            return None

    def embed_batch(self, texts: Iterable[str], *, text_type: str = "document") -> list[np.ndarray | None]:
        return [self.safe_embed_text(text, text_type=text_type) for text in texts]
