"""Keyword + dense retrieval for internal construction documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import sqrt
from typing import Iterable

import numpy as np

from backend.core.contracts import DocumentRecord
from backend.core.evidence import EvidenceItem
from backend.embedding.ali_embedding import AliTextEmbedding
from backend.search.chunker.mason_chunker import MasonChunker


@dataclass
class ChunkCandidate:
    title: str
    source: str
    citation: str
    content: str
    score: float


class HybridSearch:
    """Simple hybrid search that prefers evidence with keyword and semantic overlap."""

    def __init__(self, embedder: AliTextEmbedding | None = None) -> None:
        self.chunker = MasonChunker()
        self.embedder = embedder or AliTextEmbedding()

    def search(self, question: str, documents: Iterable[DocumentRecord], limit: int = 4) -> list[EvidenceItem]:
        query_embedding = self.embedder.safe_embed_text(question, text_type="query")
        query_terms = self._build_query_terms(question)
        candidates: list[ChunkCandidate] = []

        for document in documents:
            chunks = self.chunker.chunk(document.content)
            for index, chunk in enumerate(chunks, start=1):
                keyword_score = self._keyword_score(question, chunk, query_terms)
                semantic_score = self._semantic_score(query_embedding, chunk)
                score = keyword_score * 0.55 + semantic_score * 0.45
                if score <= 0:
                    continue

                candidates.append(
                    ChunkCandidate(
                        title=document.title,
                        source=document.source,
                        citation=f"{document.source}#chunk-{index}",
                        content=chunk,
                        score=round(score, 4),
                    )
                )

        ranked = sorted(candidates, key=lambda item: item.score, reverse=True)[:limit]
        return [
            EvidenceItem(
                title=item.title,
                source=item.source,
                snippet=item.content[:240],
                citation=item.citation,
                score=item.score,
            )
            for item in ranked
        ]

    def _keyword_score(self, question: str, chunk: str, query_terms: set[str]) -> float:
        normalized_chunk = chunk.lower()
        matches = sum(1 for term in query_terms if term in normalized_chunk)
        direct_match_bonus = 2 if question[:8] and question[:8] in chunk else 0
        return matches + direct_match_bonus

    def _semantic_score(self, query_embedding: np.ndarray | None, chunk: str) -> float:
        if query_embedding is None:
            return 0.0

        chunk_embedding = self.embedder.safe_embed_text(chunk, text_type="document")
        if chunk_embedding is None:
            return 0.0

        numerator = float(np.dot(query_embedding, chunk_embedding))
        denominator = sqrt(float(np.dot(query_embedding, query_embedding))) * sqrt(
            float(np.dot(chunk_embedding, chunk_embedding))
        )
        if not denominator:
            return 0.0
        return numerator / denominator

    def _build_query_terms(self, question: str) -> set[str]:
        lowered = question.lower().strip()
        if not lowered:
            return set()

        terms: set[str] = set()
        for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9\.-]+", lowered):
            cleaned = token.strip()
            if not cleaned:
                continue
            terms.add(cleaned)
            if re.fullmatch(r"[\u4e00-\u9fff]+", cleaned):
                for size in range(2, min(5, len(cleaned) + 1)):
                    for start in range(0, len(cleaned) - size + 1):
                        terms.add(cleaned[start : start + size])
        return {term for term in terms if len(term) >= 2}
