"""Document storage and ingestion service backed by the GraphRAG core."""

from __future__ import annotations

from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select

from backend.config.settings import settings
from backend.core.contracts import DocumentRecord, DocumentSummary, IngestResponse
from backend.graphrag_core.db.session import db_session
from backend.graphrag_core.integrations.object_storage import ObjectStorageService
from backend.graphrag_core.models.persistence import ChunkModel, DocumentBuildStateModel, DocumentModel
from backend.graphrag_core.pipelines.ingestion import DocumentIngestionPipeline
from backend.graphrag_core.runtime import bootstrap_runtime
from backend.graphrag_core.tasks.job_store import JobStore
from backend.graphrag_core.tasks.workflows import ingest_document_task
from backend.pipelines.document_processor import DocumentProcessor


class DocumentService:
    """Persist and retrieve internal documents from the database."""

    def __init__(self) -> None:
        bootstrap_runtime()
        self.processor = DocumentProcessor()
        self.storage = ObjectStorageService()
        self.pipeline = DocumentIngestionPipeline()
        self.job_store = JobStore()

    def list_documents(self, user_role: str) -> list[DocumentSummary]:
        with db_session() as session:
            documents = self._visible_documents(session, user_role)
            return [self._to_summary(record) for record in documents]

    def list_full_documents(self, user_role: str) -> list[DocumentRecord]:
        with db_session() as session:
            documents = self._visible_documents(session, user_role)
            return [self._to_record(record) for record in documents]

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
            summary = self._to_summary(document)

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

    def _to_record(self, record: DocumentModel) -> DocumentRecord:
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
            updated_at=record.updated_at,
        )

    def _to_summary(self, record: DocumentModel) -> DocumentSummary:
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
            updated_at=record.updated_at,
        )
