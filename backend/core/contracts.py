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
    file_size: int = 0
    char_count: int = 0
    chunk_count: int = 0
    progress: float = 0.0
    created_at: datetime
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
    file_size: int = 0
    char_count: int = 0
    chunk_count: int = 0
    progress: float = 0.0
    created_at: datetime
    updated_at: datetime


class IngestResponse(MasonBaseModel):
    document_id: str
    status: str
    indexed_chunks: int
    job_id: str | None = None


class ChunkingConfig(MasonBaseModel):
    mode: Literal["general"] = "general"
    separator: str = "\\n\\n"
    max_length: int = Field(default=1024, ge=200, le=4000)
    overlap: int = Field(default=50, ge=0, le=1000)
    normalize_whitespace: bool = False
    strip_urls_emails: bool = False


class RetrievalConfig(MasonBaseModel):
    mode: QaMode = "hybrid"
    semantic_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold_enabled: bool = False
    score_threshold: float = Field(default=0.5, ge=0.0, le=5.0)


class KnowledgeBaseSettings(MasonBaseModel):
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)


class ChunkPreviewRequest(MasonBaseModel):
    chunking: ChunkingConfig | None = None
    limit: int = Field(default=8, ge=1, le=20)


class ChunkPreviewItem(MasonBaseModel):
    index: int
    content: str
    character_count: int


class ChunkPreviewResponse(MasonBaseModel):
    document_id: str
    title: str
    total_chunks: int
    total_characters: int
    chunks: list[ChunkPreviewItem]


class RetrievalTestRequest(MasonBaseModel):
    question: str
    retrieval: RetrievalConfig | None = None


class RetrievalTestHit(MasonBaseModel):
    rank: int
    title: str
    source: str
    citation: str
    chunk_label: str
    snippet: str
    character_count: int
    score: float


class RetrievalTestResponse(MasonBaseModel):
    question: str
    mode: str
    duration_ms: int
    total_hits: int
    hits: list[RetrievalTestHit]
    debug: dict[str, Any] | None = None


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
