"""Document ingestion pipeline with chunking, embeddings, graph build, and community refresh."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.embedding.ali_embedding import AliTextEmbedding
from backend.graphrag_core.knowledge_base import KnowledgeBaseSettingsStore
from backend.graphrag_core.community.builder import CommunityBuilder
from backend.graphrag_core.graph.builder import GraphBuilder
from backend.graphrag_core.integrations.neo4j_store import Neo4jGraphStore
from backend.graphrag_core.models.persistence import ChunkModel, CommunityModel, DocumentModel
from backend.graphrag_core.pipelines.versioning import VersioningService
from backend.pipelines.document_processor import DocumentProcessor


class DocumentIngestionPipeline:
    """Run the core ingestion workflow for a document."""

    def __init__(self) -> None:
        self.processor = DocumentProcessor()
        self.embedder = AliTextEmbedding()
        self.graph_builder = GraphBuilder()
        self.community_builder = CommunityBuilder()
        self.neo4j_store = Neo4jGraphStore()
        self.versioning = VersioningService()
        self.settings_store = KnowledgeBaseSettingsStore()

    def ingest_document(self, session: Session, document_id: str) -> dict[str, int | str]:
        """Ingest one document and refresh related graph/index artifacts."""

        document = session.execute(
            select(DocumentModel).where(DocumentModel.document_id == document_id)
        ).scalar_one_or_none()
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        unchanged, build_state = self.versioning.is_document_unchanged(session, document)
        if unchanged:
            community_count = len(session.execute(select(CommunityModel)).scalars().all())
            return {
                "document_id": document.document_id,
                "indexed_chunks": build_state.chunk_count if build_state else 0,
                "entities": build_state.entity_count if build_state else 0,
                "relations": build_state.relation_count if build_state else 0,
                "communities": community_count,
                "status": "up_to_date",
            }

        document.ingestion_status = "processing"
        document.processing_errors = []
        session.execute(delete(ChunkModel).where(ChunkModel.document_pk == document.pk))
        session.flush()

        chunks = self.processor.chunk_preview(document.content, self.settings_store.load().chunking)
        chunk_rows: list[ChunkModel] = []
        for index, chunk in enumerate(chunks, start=1):
            vector = self.embedder.safe_embed_text(chunk, text_type="document")
            chunk_row = ChunkModel(
                document_pk=document.pk,
                chunk_index=index,
                content=chunk,
                citation=f"{document.source}#chunk-{index}",
                embedding=vector.tolist() if vector is not None else None,
            )
            session.add(chunk_row)
            chunk_rows.append(chunk_row)
        session.flush()

        document.status = "indexed"
        document.ingestion_status = "indexed"
        document.version += 1
        document.graph_version += 1
        document.index_version += 1

        graph_stats = self.graph_builder.rebuild_document_graph(session, document, chunk_rows)
        community_count = self.community_builder.rebuild(session)
        community_rows = session.execute(select(CommunityModel)).scalars().all()
        self.neo4j_store.sync_document(session, document)
        self.neo4j_store.sync_communities(community_rows)
        self.versioning.record_success(
            session,
            document=document,
            chunk_count=len(chunk_rows),
            entity_count=graph_stats["entities"],
            relation_count=graph_stats["relations"],
        )

        return {
            "document_id": document.document_id,
            "indexed_chunks": len(chunk_rows),
            "entities": graph_stats["entities"],
            "relations": graph_stats["relations"],
            "communities": community_count,
            "status": document.ingestion_status,
        }
