"""Embedding abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseEmbedding(ABC):
    """Minimal interface for dense embeddings."""

    @abstractmethod
    def embed_text(self, text: str, *, text_type: str = "document") -> np.ndarray | None:
        raise NotImplementedError

