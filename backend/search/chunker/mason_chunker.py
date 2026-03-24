"""Construction-domain aware text chunker."""

from __future__ import annotations

import re

from backend.config.constants import CHUNK_SIZE, OVERLAP
from backend.search.chunker.base_chunker import BaseChunker


class MasonChunker(BaseChunker):
    """Chunk text while preserving standards and numbered procedures."""

    sentence_pattern = re.compile(r"(?<=[。！？；;\n])")

    def chunk(self, text: str) -> list[str]:
        clean_text = re.sub(r"\s+", " ", text).strip()
        if not clean_text:
            return []

        pieces = [part.strip() for part in self.sentence_pattern.split(clean_text) if part.strip()]
        chunks: list[str] = []
        current = ""
        for piece in pieces:
            if len(current) + len(piece) <= CHUNK_SIZE:
                current += piece
                continue

            if current:
                chunks.append(current)
                overlap_text = current[-OVERLAP:] if len(current) > OVERLAP else current
                current = f"{overlap_text}{piece}"
            else:
                chunks.append(piece[:CHUNK_SIZE])
                current = piece[CHUNK_SIZE - OVERLAP :]

        if current:
            chunks.append(current)

        return chunks
