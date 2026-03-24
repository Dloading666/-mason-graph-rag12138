"""Celery tasks for ingestion and long-form research reports."""

from __future__ import annotations

from backend.graphrag_core.agents.orchestrator import AgentRouter
from backend.graphrag_core.db.session import db_session
from backend.graphrag_core.pipelines.ingestion import DocumentIngestionPipeline
from backend.graphrag_core.tasks.celery_app import celery_app
from backend.graphrag_core.tasks.job_store import JobStore


@celery_app.task(name="backend.graphrag_core.tasks.ingest_document")
def ingest_document_task(job_id: str, document_id: str) -> dict:
    """Ingest a document in the background."""

    job_store = JobStore()
    pipeline = DocumentIngestionPipeline()
    with db_session() as session:
        job_store.mark_running(session, job_id, progress=0.2)
        result = pipeline.ingest_document(session, document_id)
        job_store.mark_completed(session, job_id, result=result)
        return result


@celery_app.task(name="backend.graphrag_core.tasks.generate_report")
def generate_report_task(job_id: str, question: str, user_role: str, requested_mode: str = "fusion") -> dict:
    """Generate a longer report using the fusion agent path."""

    job_store = JobStore()
    router = AgentRouter()
    with db_session() as session:
        job_store.mark_running(session, job_id, progress=0.2)
        answer = router.resolve(requested_mode).run(
            session,
            question=question,
            user_role=user_role,
            requested_mode=requested_mode,
            need_evidence=True,
            debug_enabled=True,
        )
        result = {
            "answer": answer.answer,
            "mode": answer.mode,
            "trace_id": answer.trace_id,
            "citations": answer.citations,
            "plan": answer.plan,
            "execution_summary": answer.execution_summary,
        }
        job_store.mark_completed(session, job_id, result=result)
        return result
