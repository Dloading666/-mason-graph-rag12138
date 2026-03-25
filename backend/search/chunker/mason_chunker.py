"""Construction-domain aware text chunker."""

from __future__ import annotations

import re

from backend.config.constants import CHUNK_SIZE, OVERLAP
from backend.core.contracts import ChunkingConfig
from backend.search.chunker.base_chunker import BaseChunker


class MasonChunker(BaseChunker):
    """Chunk text while preserving standards and numbered procedures."""

    sentence_pattern = re.compile(r"(?<=[銆傦紒锛燂紱;\n])")
    url_email_pattern = re.compile(r"(https?://\S+|www\.\S+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig(max_length=CHUNK_SIZE, overlap=OVERLAP)

    def chunk(self, text: str) -> list[str]:
        clean_text = self._preprocess(text)
        if not clean_text:
            return []

        pieces = self._split_pieces(clean_text)
        max_length = self.config.max_length
        overlap = min(self.config.overlap, max_length - 1) if max_length > 1 else 0

        chunks: list[str] = []
        current = ""
        for piece in pieces:
            if len(piece) > max_length:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._slice_large_piece(piece, max_length, overlap))
                continue

            if len(current) + len(piece) <= max_length:
                current += piece
                continue

            if current:
                chunks.append(current)
                overlap_text = current[-overlap:] if overlap and len(current) > overlap else current
                current = f"{overlap_text}{piece}"
            else:
                chunks.extend(self._slice_large_piece(piece, max_length, overlap))

        if current:
            chunks.append(current)

        return chunks

    def _preprocess(self, text: str) -> str:
        clean_text = text.strip()
        if self.config.strip_urls_emails:
            clean_text = self.url_email_pattern.sub(" ", clean_text)
        if self.config.normalize_whitespace:
            clean_text = re.sub(r"\s+", " ", clean_text)
        return clean_text.strip()

    def _split_pieces(self, text: str) -> list[str]:
        separator = self._decode_separator(self.config.separator)
        if separator and separator in text:
            return [part.strip() for part in text.split(separator) if part.strip()]
        return [part.strip() for part in self.sentence_pattern.split(text) if part.strip()]

    def _decode_separator(self, separator: str) -> str:
        try:
            return separator.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            return separator

    def _slice_large_piece(self, piece: str, max_length: int, overlap: int) -> list[str]:
        if len(piece) <= max_length:
            return [piece]

        step = max(max_length - overlap, 1)
        return [piece[start : start + max_length] for start in range(0, len(piece), step)]
