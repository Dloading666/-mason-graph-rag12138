"""Document ingestion scaffold."""

from __future__ import annotations

from backend.core.contracts import DocumentRecord
from backend.graph.incremental_update import IncrementalGraphUpdater
from backend.pipelines.document_processor import DocumentProcessor


class IngestionPipeline:
    """Coordinate preview chunking and graph sync placeholders."""

    def __init__(self) -> None:
        self.processor = DocumentProcessor()
        self.graph_updater = IncrementalGraphUpdater()

    def run(self, document: DocumentRecord) -> dict[str, object]:
        return {
            "document_id": document.document_id,
            "chunks": self.processor.chunk_preview(document.content),
            "graph_sync": self.graph_updater.upsert(document),
        }

