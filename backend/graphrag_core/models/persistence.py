"""SQLAlchemy models for documents, graph artifacts, jobs, and traces."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.graphrag_core.db.base import Base


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


class TimestampMixin:
    """Shared timestamps for persisted records."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DocumentModel(Base, TimestampMixin):
    """Canonical metadata for an ingested enterprise document."""

    __tablename__ = "documents"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: f"doc-{uuid4().hex[:12]}")
    title: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(128), default="general")
    content: Mapped[str] = mapped_column(Text)
    object_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allowed_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    ingestion_status: Mapped[str] = mapped_column(String(32), default="pending")
    version: Mapped[int] = mapped_column(Integer, default=1)
    graph_version: Mapped[int] = mapped_column(Integer, default=0)
    index_version: Mapped[int] = mapped_column(Integer, default=0)
    processing_errors: Mapped[list[str]] = mapped_column(JSON, default=list)

    chunks: Mapped[list["ChunkModel"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    mentions: Mapped[list["MentionModel"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ChunkModel(Base):
    """Text chunk plus optional embedding generated from a document."""

    __tablename__ = "chunks"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: f"chunk-{uuid4().hex[:12]}")
    document_pk: Mapped[int] = mapped_column(ForeignKey("documents.pk", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    citation: Mapped[str] = mapped_column(String(255))
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped[DocumentModel] = relationship(back_populates="chunks")
    mentions: Mapped[list["MentionModel"]] = relationship(back_populates="chunk", cascade="all, delete-orphan")


class EntityModel(Base, TimestampMixin):
    """Canonical entity node extracted from documents."""

    __tablename__ = "entities"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: f"ent-{uuid4().hex[:12]}")
    canonical_name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_document_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.6)

    mentions: Mapped[list["MentionModel"]] = relationship(back_populates="entity", cascade="all, delete-orphan")


class MentionModel(Base):
    """Link between an entity and the chunk/document where it was mentioned."""

    __tablename__ = "mentions"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_pk: Mapped[int] = mapped_column(ForeignKey("documents.pk", ondelete="CASCADE"), index=True)
    chunk_pk: Mapped[int | None] = mapped_column(ForeignKey("chunks.pk", ondelete="CASCADE"), nullable=True, index=True)
    entity_pk: Mapped[int] = mapped_column(ForeignKey("entities.pk", ondelete="CASCADE"), index=True)
    mention_text: Mapped[str] = mapped_column(String(255))
    normalized_text: Mapped[str] = mapped_column(String(255), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.6)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped[DocumentModel] = relationship(back_populates="mentions")
    chunk: Mapped[ChunkModel | None] = relationship(back_populates="mentions")
    entity: Mapped[EntityModel] = relationship(back_populates="mentions")


class RelationModel(Base):
    """Directed relationship between two canonical entities."""

    __tablename__ = "relations"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relation_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: f"rel-{uuid4().hex[:12]}"
    )
    source_entity_pk: Mapped[int] = mapped_column(ForeignKey("entities.pk", ondelete="CASCADE"), index=True)
    target_entity_pk: Mapped[int] = mapped_column(ForeignKey("entities.pk", ondelete="CASCADE"), index=True)
    document_pk: Mapped[int] = mapped_column(ForeignKey("documents.pk", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CommunityModel(Base, TimestampMixin):
    """Coarse community grouping for global graph search."""

    __tablename__ = "communities"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    community_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: f"community-{uuid4().hex[:12]}"
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    source_document_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    entity_names: Mapped[list[str]] = mapped_column(JSON, default=list)
    graph_version: Mapped[int] = mapped_column(Integer, default=0)


class JobModel(Base, TimestampMixin):
    """Async workflow status, including ingestion and long-report jobs."""

    __tablename__ = "jobs"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: f"job-{uuid4().hex[:12]}")
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    document_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TraceModel(Base):
    """Persisted question-answer trace used for debugging and auditability."""

    __tablename__ = "traces"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: f"trace-{uuid4().hex[:12]}"
    )
    user_role: Mapped[str] = mapped_column(String(32), index=True)
    question: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(32), default="auto", index=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    execution_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    debug: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    citations: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FeedbackModel(Base):
    """User feedback linked to a previously generated trace."""

    __tablename__ = "feedback"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: f"feedback-{uuid4().hex[:12]}"
    )
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvaluationRunModel(Base):
    """Persisted evaluation run metadata and aggregate metrics."""

    __tablename__ = "evaluation_runs"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: f"eval-{uuid4().hex[:12]}"
    )
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DocumentBuildStateModel(Base, TimestampMixin):
    """Track incremental build state for one document."""

    __tablename__ = "document_build_states"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    content_signature: Mapped[str] = mapped_column(String(128), index=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    relation_count: Mapped[int] = mapped_column(Integer, default=0)
    graph_version: Mapped[int] = mapped_column(Integer, default=0)
    index_version: Mapped[int] = mapped_column(Integer, default=0)


class VersionSnapshotModel(Base):
    """Record graph/index version snapshots for auditing and rollback reference."""

    __tablename__ = "version_snapshots"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: f"snapshot-{uuid4().hex[:12]}"
    )
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    scope: Mapped[str] = mapped_column(String(32), index=True)
    version_number: Mapped[int] = mapped_column(Integer, index=True)
    content_signature: Mapped[str] = mapped_column(String(128), index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
