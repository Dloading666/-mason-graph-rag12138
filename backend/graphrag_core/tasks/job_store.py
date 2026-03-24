"""Persistence helpers for async jobs."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.graphrag_core.models.persistence import JobModel


class JobStore:
    """Create, update, and fetch ingestion/report jobs."""

    def create_job(
        self,
        session: Session,
        *,
        job_type: str,
        payload: dict,
        document_id: str | None = None,
        trace_id: str | None = None,
        status: str = "queued",
    ) -> JobModel:
        job = JobModel(
            job_type=job_type,
            payload=payload,
            document_id=document_id,
            trace_id=trace_id,
            status=status,
            progress=0.0,
        )
        session.add(job)
        session.flush()
        return job

    def get_job(self, session: Session, job_id: str) -> JobModel | None:
        return session.execute(select(JobModel).where(JobModel.job_id == job_id)).scalar_one_or_none()

    def mark_running(self, session: Session, job_id: str, *, progress: float = 0.1) -> JobModel | None:
        job = self.get_job(session, job_id)
        if job is None:
            return None
        job.status = "running"
        job.progress = progress
        return job

    def mark_completed(self, session: Session, job_id: str, *, result: dict, progress: float = 1.0) -> JobModel | None:
        job = self.get_job(session, job_id)
        if job is None:
            return None
        job.status = "completed"
        job.result = result
        job.progress = progress
        job.finished_at = datetime.now(UTC)
        return job

    def mark_failed(self, session: Session, job_id: str, *, error_message: str) -> JobModel | None:
        job = self.get_job(session, job_id)
        if job is None:
            return None
        job.status = "failed"
        job.error_message = error_message
        job.finished_at = datetime.now(UTC)
        return job
