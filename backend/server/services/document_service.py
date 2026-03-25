"""Document storage, knowledge-base settings, and retrieval testing services."""

from __future__ import annotations

import re
from time import perf_counter
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, select

from backend.config.settings import settings
from backend.core.contracts import (
    ChunkPreviewItem,
    ChunkPreviewResponse,
    DocumentRecord,
    DocumentSummary,
    IngestResponse,
    KnowledgeBaseSettings,
    RetrievalConfig,
    RetrievalTestHit,
    RetrievalTestRequest,
    RetrievalTestResponse,
)
from backend.graphrag_core.db.session import db_session
from backend.graphrag_core.integrations.object_storage import ObjectStorageService
from backend.graphrag_core.knowledge_base import KnowledgeBaseSettingsStore
from backend.graphrag_core.models.persistence import ChunkModel, DocumentBuildStateModel, DocumentModel, JobModel
from backend.graphrag_core.pipelines.ingestion import DocumentIngestionPipeline
from backend.graphrag_core.runtime import bootstrap_runtime
from backend.graphrag_core.search.modes import MultiModeSearchService
from backend.graphrag_core.tasks.job_store import JobStore
from backend.graphrag_core.tasks.workflows import ingest_document_task
from backend.pipelines.document_processor import DocumentProcessor


class DocumentService:
    """Persist documents and expose knowledge-base management capabilities."""

    chunk_citation_pattern = re.compile(r"#chunk-(\d+)$", re.IGNORECASE)

    def __init__(self) -> None:
        bootstrap_runtime()
        self.processor = DocumentProcessor()
        self.storage = ObjectStorageService()
        self.pipeline = DocumentIngestionPipeline()
        self.job_store = JobStore()
        self.settings_store = KnowledgeBaseSettingsStore()
        self.search_service = MultiModeSearchService()

    def list_documents(self, user_role: str) -> list[DocumentSummary]:
        with db_session() as session:
            documents = self._visible_documents(session, user_role)
            latest_jobs = self._latest_jobs_by_document(session, [record.document_id for record in documents])
            chunk_counts = self._chunk_counts_by_document(session, [record.pk for record in documents])
            return [
                self._to_summary(
                    record,
                    chunk_count=chunk_counts.get(record.pk, 0),
                    file_size=self._derive_file_size(record),
                    progress=self._resolve_progress(record, latest_jobs.get(record.document_id)),
                )
                for record in documents
            ]

    def list_full_documents(self, user_role: str) -> list[DocumentRecord]:
        with db_session() as session:
            documents = self._visible_documents(session, user_role)
            latest_jobs = self._latest_jobs_by_document(session, [record.document_id for record in documents])
            chunk_counts = self._chunk_counts_by_document(session, [record.pk for record in documents])
            return [
                self._to_record(
                    record,
                    chunk_count=chunk_counts.get(record.pk, 0),
                    file_size=self._derive_file_size(record),
                    progress=self._resolve_progress(record, latest_jobs.get(record.document_id)),
                )
                for record in documents
            ]

    def get_settings(self) -> KnowledgeBaseSettings:
        return self.settings_store.load()

    def update_settings(self, payload: KnowledgeBaseSettings) -> KnowledgeBaseSettings:
        self._validate_settings(payload)
        return self.settings_store.save(payload)

    def preview_chunks(
        self,
        document_id: str,
        *,
        user_role: str,
        settings_override: KnowledgeBaseSettings | None = None,
        limit: int = 8,
    ) -> ChunkPreviewResponse:
        effective_settings = settings_override or self.settings_store.load()
        self._validate_settings(effective_settings)
        chunking_config = effective_settings.chunking

        with db_session() as session:
            document = self._get_visible_document(session, document_id, user_role)
            if document is None:
                raise LookupError("Document not found")

            chunks = self.processor.chunk_preview(document.content, chunking_config)
            return ChunkPreviewResponse(
                document_id=document.document_id,
                title=document.title,
                total_chunks=len(chunks),
                total_characters=sum(len(chunk) for chunk in chunks),
                chunks=[
                    ChunkPreviewItem(index=index, content=chunk, character_count=len(chunk))
                    for index, chunk in enumerate(chunks[:limit], start=1)
                ],
            )

    def run_retrieval_test(self, payload: RetrievalTestRequest, user_role: str) -> RetrievalTestResponse:
        retrieval = payload.retrieval or self.settings_store.load().retrieval
        self._validate_retrieval_config(retrieval)

        with db_session() as session:
            started_at = perf_counter()
            result = self.search_service.search(
                session,
                question=payload.question,
                user_role=user_role,
                requested_mode=retrieval.mode,
                limit=retrieval.top_k,
                semantic_weight=retrieval.semantic_weight,
                keyword_weight=retrieval.keyword_weight,
                score_threshold=retrieval.score_threshold if retrieval.score_threshold_enabled else None,
            )
            duration_ms = int((perf_counter() - started_at) * 1000)

        hits = [
            self._to_retrieval_hit(index=index, title=item.title, source=item.source, citation=item.citation, snippet=item.snippet, score=item.score)
            for index, item in enumerate(result.evidence, start=1)
        ]

        return RetrievalTestResponse(
            question=payload.question,
            mode=result.mode,
            duration_ms=duration_ms,
            total_hits=len(hits),
            hits=hits,
            debug=result.debug,
        )

    async def save_upload(
        self,
        upload_file: UploadFile,
        *,
        category: str,
        allowed_roles: list[str],
    ) -> DocumentSummary:
        raw_bytes = await upload_file.read()
        await upload_file.seek(0)
        content = await self.processor.extract_text(upload_file)

        suffix = (upload_file.filename or ".txt").split(".")[-1]
        object_key = f"documents/{uuid4().hex}.{suffix}"
        self.storage.save_bytes(object_key, raw_bytes)

        queued_job_id: str | None = None
        with db_session() as session:
            document = DocumentModel(
                title=(upload_file.filename or "upload").rsplit(".", 1)[0],
                source=upload_file.filename or object_key,
                category=category,
                content=content,
                object_key=object_key,
                allowed_roles=allowed_roles,
                status="uploaded",
                ingestion_status="queued" if settings.ENABLE_ASYNC_INGESTION else "pending",
            )
            session.add(document)
            session.flush()
            document_id = document.document_id

            if settings.ENABLE_ASYNC_INGESTION:
                job = self.job_store.create_job(
                    session,
                    job_type="document_ingestion",
                    payload={"document_id": document_id},
                    document_id=document_id,
                )
                queued_job_id = job.job_id
            else:
                self.pipeline.ingest_document(session, document_id)

            session.refresh(document)
            summary = self._to_summary(
                document,
                chunk_count=0,
                file_size=len(raw_bytes),
                progress=0.05 if queued_job_id else 1.0,
            )

        if queued_job_id is not None:
            ingest_document_task.delay(queued_job_id, document_id)
        return summary

    def delete_document(self, document_id: str) -> None:
        with db_session() as session:
            document = session.execute(
                select(DocumentModel).where(DocumentModel.document_id == document_id)
            ).scalar_one_or_none()
            if document is None:
                raise ValueError("Document not found")
            if document.object_key:
                self.storage.delete(document.object_key)
            session.delete(document)

    def ingest_document(self, document_id: str) -> IngestResponse:
        queued_job_id: str | None = None
        with db_session() as session:
            document = session.execute(
                select(DocumentModel).where(DocumentModel.document_id == document_id)
            ).scalar_one_or_none()
            if document is None:
                raise ValueError("Document not found")

            if settings.ENABLE_ASYNC_INGESTION and not settings.CELERY_TASK_ALWAYS_EAGER:
                job = self.job_store.create_job(
                    session,
                    job_type="document_ingestion",
                    payload={"document_id": document.document_id},
                    document_id=document.document_id,
                )
                queued_job_id = job.job_id
                document.ingestion_status = "queued"
                response = IngestResponse(document_id=document_id, status="queued", indexed_chunks=0, job_id=job.job_id)
            else:
                result = self.pipeline.ingest_document(session, document.document_id)
                response = IngestResponse(
                    document_id=document_id,
                    status=str(result["status"]),
                    indexed_chunks=int(result["indexed_chunks"]),
                )

        if queued_job_id is not None:
            ingest_document_task.delay(queued_job_id, document_id)
        return response

    def ensure_ready_documents(self, user_role: str) -> None:
        with db_session() as session:
            for document in self._visible_documents(session, user_role):
                indexed_chunk = session.execute(
                    select(ChunkModel.pk).where(ChunkModel.document_pk == document.pk).limit(1)
                ).scalar_one_or_none()
                build_state = session.execute(
                    select(DocumentBuildStateModel.pk)
                    .where(DocumentBuildStateModel.document_id == document.document_id)
                    .limit(1)
                ).scalar_one_or_none()
                if document.status == "indexed" and (indexed_chunk is None or build_state is None):
                    self.pipeline.ingest_document(session, document.document_id)

    def _visible_documents(self, session, user_role: str) -> list[DocumentModel]:
        documents = session.execute(select(DocumentModel).order_by(DocumentModel.updated_at.desc())).scalars().all()
        if user_role == "admin":
            return documents
        return [record for record in documents if user_role in (record.allowed_roles or [])]

    def _get_visible_document(self, session, document_id: str, user_role: str) -> DocumentModel | None:
        return next((record for record in self._visible_documents(session, user_role) if record.document_id == document_id), None)

    def _chunk_counts_by_document(self, session, document_pks: list[int]) -> dict[int, int]:
        if not document_pks:
            return {}

        rows = session.execute(
            select(ChunkModel.document_pk, func.count(ChunkModel.pk))
            .where(ChunkModel.document_pk.in_(document_pks))
            .group_by(ChunkModel.document_pk)
        ).all()
        return {int(document_pk): int(count) for document_pk, count in rows}

    def _latest_jobs_by_document(self, session, document_ids: list[str]) -> dict[str, JobModel]:
        if not document_ids:
            return {}

        rows = session.execute(
            select(JobModel)
            .where(JobModel.document_id.in_(document_ids))
            .order_by(JobModel.created_at.desc())
        ).scalars().all()
        latest_jobs: dict[str, JobModel] = {}
        for row in rows:
            if row.document_id and row.document_id not in latest_jobs:
                latest_jobs[row.document_id] = row
        return latest_jobs

    def _resolve_progress(self, record: DocumentModel, job: JobModel | None) -> float:
        if record.ingestion_status in {"indexed", "up_to_date"}:
            return 1.0
        if job is not None:
            return float(job.progress or 0.0)
        if record.ingestion_status == "processing":
            return 0.4
        if record.ingestion_status == "queued":
            return 0.05
        return 0.0

    def _derive_file_size(self, record: DocumentModel) -> int:
        stored_size = self.storage.get_size(record.object_key)
        if stored_size > 0:
            return stored_size
        return len((record.content or "").encode("utf-8"))

    def _validate_settings(self, payload: KnowledgeBaseSettings) -> None:
        if payload.chunking.overlap >= payload.chunking.max_length:
            raise ValueError("Chunk overlap must be smaller than the max length")
        self._validate_retrieval_config(payload.retrieval)

    def _validate_retrieval_config(self, payload: RetrievalConfig) -> None:
        if payload.semantic_weight + payload.keyword_weight <= 0:
            raise ValueError("Semantic and keyword weights cannot both be zero")

    def _to_retrieval_hit(
        self,
        *,
        index: int,
        title: str,
        source: str,
        citation: str,
        snippet: str,
        score: float,
    ) -> RetrievalTestHit:
        matched_chunk = self.chunk_citation_pattern.search(citation)
        chunk_label = f"Chunk #{matched_chunk.group(1)}" if matched_chunk else "匹配片段"
        return RetrievalTestHit(
            rank=index,
            title=title,
            source=source,
            citation=citation,
            chunk_label=chunk_label,
            snippet=snippet,
            character_count=len(snippet),
            score=round(score, 4),
        )

    def _to_record(
        self,
        record: DocumentModel,
        *,
        chunk_count: int,
        file_size: int,
        progress: float,
    ) -> DocumentRecord:
        return DocumentRecord(
            document_id=record.document_id,
            title=record.title,
            source=record.source,
            category=record.category,
            content=record.content,
            allowed_roles=record.allowed_roles or [],
            status=record.status,
            ingestion_status=record.ingestion_status,
            version=record.version,
            graph_version=record.graph_version,
            index_version=record.index_version,
            processing_errors=record.processing_errors or [],
            file_size=file_size,
            char_count=len(record.content or ""),
            chunk_count=chunk_count,
            progress=progress,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _to_summary(
        self,
        record: DocumentModel,
        *,
        chunk_count: int,
        file_size: int,
        progress: float,
    ) -> DocumentSummary:
        return DocumentSummary(
            document_id=record.document_id,
            title=record.title,
            source=record.source,
            category=record.category,
            allowed_roles=record.allowed_roles or [],
            status=record.status,
            ingestion_status=record.ingestion_status,
            version=record.version,
            graph_version=record.graph_version,
            index_version=record.index_version,
            processing_errors=record.processing_errors or [],
            file_size=file_size,
            char_count=len(record.content or ""),
            chunk_count=chunk_count,
            progress=progress,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
