"""API contracts shared across services and endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from backend.core.base_model import MasonBaseModel
from backend.core.evidence import EvidenceItem


QaMode = Literal["auto", "naive", "local", "global", "hybrid", "deep_research", "fusion"]


class UserProfile(MasonBaseModel):
    username: str
    display_name: str
    role: str


class LoginRequest(MasonBaseModel):
    username: str
    password: str


class LoginResponse(MasonBaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class QaRequest(MasonBaseModel):
    question: str
    need_evidence: bool = True
    mode: QaMode = "auto"
    debug: bool = False


class QaResponse(MasonBaseModel):
    answer: str
    evidence: list[EvidenceItem]
    citations: list[str]
    trace_id: str
    mode: str = "auto"
    plan: dict[str, Any] | None = None
    execution_summary: dict[str, Any] | None = None
    debug: dict[str, Any] | None = None


class DocumentRecord(MasonBaseModel):
    document_id: str
    title: str
    source: str
    category: str
    content: str
    allowed_roles: list[str]
    status: str
    ingestion_status: str = "pending"
    version: int
    graph_version: int = 0
    index_version: int = 0
    processing_errors: list[str] = []
    updated_at: datetime


class DocumentSummary(MasonBaseModel):
    document_id: str
    title: str
    source: str
    category: str
    allowed_roles: list[str]
    status: str
    ingestion_status: str = "pending"
    version: int
    graph_version: int = 0
    index_version: int = 0
    processing_errors: list[str] = []
    updated_at: datetime


class IngestResponse(MasonBaseModel):
    document_id: str
    status: str
    indexed_chunks: int
    job_id: str | None = None


class GraphNode(MasonBaseModel):
    id: str
    name: str
    category: str
    source_documents: list[str]


class GraphEdge(MasonBaseModel):
    source: str
    target: str
    relation: str
    weight: float = 1.0


class GraphCommunity(MasonBaseModel):
    community_id: str
    name: str
    category: str
    summary: str
    source_documents: list[str]
    entity_names: list[str]


class GraphResponse(MasonBaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    communities: list[GraphCommunity] = []
    source_documents: list[str]
    entity_neighbors: dict[str, list[str]] = {}


class ResearchRequest(MasonBaseModel):
    question: str
    mode: QaMode = "fusion"


class ResearchJobResponse(MasonBaseModel):
    job_id: str
    status: str


class JobResponse(MasonBaseModel):
    job_id: str
    job_type: str
    status: str
    progress: float
    document_id: str | None = None
    trace_id: str | None = None
    result: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None = None


class TraceResponse(MasonBaseModel):
    trace_id: str
    question: str
    user_role: str
    mode: str
    answer: str | None = None
    plan: dict[str, Any] | None = None
    execution_summary: dict[str, Any] | None = None
    debug: dict[str, Any] | None = None
    citations: list[str] = []
    created_at: datetime


class FeedbackRequest(MasonBaseModel):
    trace_id: str
    rating: int | None = None
    sentiment: str | None = None
    comment: str | None = None


class FeedbackResponse(MasonBaseModel):
    feedback_id: str
    trace_id: str
    status: str = "received"


class EvaluationRunRequest(MasonBaseModel):
    name: str = "baseline-evaluation"
    modes: list[QaMode] = Field(default_factory=lambda: ["naive", "hybrid", "fusion"])


class EvaluationRunResponse(MasonBaseModel):
    run_id: str
    name: str
    status: str
    metrics: dict[str, Any]
    notes: str | None = None
    created_at: datetime
    finished_at: datetime | None = None
