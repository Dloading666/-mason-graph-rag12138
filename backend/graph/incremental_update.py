"""Scaffold for future graph incremental updates."""

from __future__ import annotations

from backend.core.contracts import DocumentRecord


class IncrementalGraphUpdater:
    """Placeholder for Neo4j write-side synchronization."""

    def upsert(self, document: DocumentRecord) -> dict[str, str]:
        return {
            "document_id": document.document_id,
            "status": "skipped",
            "message": "Neo4j incremental sync is scaffolded but not enabled in v1.",
        }

