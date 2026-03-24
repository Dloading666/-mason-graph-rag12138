"""Incremental build-state helpers for graph and index version management."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.graphrag_core.models.persistence import DocumentBuildStateModel, DocumentModel, VersionSnapshotModel


class VersioningService:
    """Manage content signatures and version snapshots for incremental ingestion."""

    def calculate_signature(self, content: str) -> str:
        """Return a stable content hash used to detect document deltas."""

        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def is_document_unchanged(self, session: Session, document: DocumentModel) -> tuple[bool, DocumentBuildStateModel | None]:
        """Check whether the document content matches the latest successful build."""

        state = session.execute(
            select(DocumentBuildStateModel).where(DocumentBuildStateModel.document_id == document.document_id)
        ).scalar_one_or_none()
        if state is None:
            return False, None
        return state.content_signature == self.calculate_signature(document.content), state

    def record_success(
        self,
        session: Session,
        *,
        document: DocumentModel,
        chunk_count: int,
        entity_count: int,
        relation_count: int,
    ) -> DocumentBuildStateModel:
        """Persist the latest successful build metadata and append snapshots."""

        signature = self.calculate_signature(document.content)
        state = session.execute(
            select(DocumentBuildStateModel).where(DocumentBuildStateModel.document_id == document.document_id)
        ).scalar_one_or_none()
        if state is None:
            state = DocumentBuildStateModel(
                document_id=document.document_id,
                content_signature=signature,
            )
            session.add(state)
            session.flush()

        state.content_signature = signature
        state.chunk_count = chunk_count
        state.entity_count = entity_count
        state.relation_count = relation_count
        state.graph_version = document.graph_version
        state.index_version = document.index_version

        summary = f"chunks={chunk_count}, entities={entity_count}, relations={relation_count}"
        session.add(
            VersionSnapshotModel(
                document_id=document.document_id,
                scope="graph",
                version_number=document.graph_version,
                content_signature=signature,
                metrics={
                    "entities": entity_count,
                    "relations": relation_count,
                },
                change_summary=summary,
            )
        )
        session.add(
            VersionSnapshotModel(
                document_id=document.document_id,
                scope="index",
                version_number=document.index_version,
                content_signature=signature,
                metrics={
                    "chunks": chunk_count,
                },
                change_summary=summary,
            )
        )
        return state
