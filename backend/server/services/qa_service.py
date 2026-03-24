"""Question answering orchestration backed by the GraphRAG core."""

from __future__ import annotations

from backend.core.contracts import QaRequest, QaResponse
from backend.graphrag_core.agents.orchestrator import AgentRouter
from backend.graphrag_core.db.session import db_session
from backend.graphrag_core.runtime import bootstrap_runtime
from backend.server.services.document_service import DocumentService


class QaService:
    """Route questions through retrieval and agent orchestration."""

    def __init__(self) -> None:
        bootstrap_runtime()
        self.document_service = DocumentService()
        self.router = AgentRouter()

    def ask(self, request: QaRequest, user_role: str) -> QaResponse:
        self.document_service.ensure_ready_documents(user_role)
        with db_session() as session:
            answer = self.router.resolve(request.mode).run(
                session,
                question=request.question,
                user_role=user_role,
                requested_mode=request.mode,
                need_evidence=request.need_evidence,
                debug_enabled=request.debug,
            )
            return QaResponse(
                answer=answer.answer,
                evidence=answer.evidence,
                citations=answer.citations,
                trace_id=answer.trace_id,
                mode=answer.mode,
                plan=answer.plan,
                execution_summary=answer.execution_summary,
                debug=answer.debug,
            )
