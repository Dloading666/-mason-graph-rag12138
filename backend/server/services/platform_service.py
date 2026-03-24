"""Platform-level services for jobs, traces, feedback, and evaluations."""

from __future__ import annotations

from sqlalchemy import select

from backend.core.contracts import (
    EvaluationRunResponse,
    FeedbackRequest,
    FeedbackResponse,
    JobResponse,
    ResearchJobResponse,
    TraceResponse,
    UserProfile,
)
from backend.graphrag_core.db.session import db_session
from backend.graphrag_core.evaluation.service import EvaluationService
from backend.graphrag_core.models.persistence import FeedbackModel, JobModel, TraceModel
from backend.graphrag_core.tasks.job_store import JobStore
from backend.graphrag_core.tasks.workflows import generate_report_task
from backend.graphrag_core.traces.store import TraceStore


class PlatformService:
    """Expose persistent platform operations to API endpoints."""

    def __init__(self) -> None:
        self.job_store = JobStore()
        self.trace_store = TraceStore()
        self.evaluation_service = EvaluationService()

    def create_research_job(self, *, question: str, mode: str, user: UserProfile) -> ResearchJobResponse:
        with db_session() as session:
            job = self.job_store.create_job(
                session,
                job_type="research_report",
                payload={"question": question, "mode": mode, "user_role": user.role},
            )
            job_id = job.job_id
            job_status = job.status
        generate_report_task.delay(job_id, question, user.role, mode)
        return ResearchJobResponse(job_id=job_id, status=job_status)

    def get_job(self, job_id: str) -> JobResponse | None:
        with db_session() as session:
            job = self.job_store.get_job(session, job_id)
            if job is None:
                return None
            return self._to_job_response(job)

    def list_jobs(self, *, user: UserProfile, limit: int = 50) -> list[JobResponse]:
        with db_session() as session:
            rows = session.execute(
                select(JobModel).order_by(JobModel.created_at.desc()).limit(limit)
            ).scalars().all()
            if user.role != "admin":
                rows = [job for job in rows if job.payload.get("user_role") == user.role or job.document_id is None]
            return [self._to_job_response(job) for job in rows]

    def get_trace(self, trace_id: str) -> TraceResponse | None:
        with db_session() as session:
            trace = self.trace_store.get_trace(session, trace_id)
            if trace is None:
                return None
            return self._to_trace_response(trace)

    def list_traces(self, *, user: UserProfile, limit: int = 50) -> list[TraceResponse]:
        with db_session() as session:
            rows = session.execute(
                select(TraceModel).order_by(TraceModel.created_at.desc()).limit(limit)
            ).scalars().all()
            if user.role != "admin":
                rows = [trace for trace in rows if trace.user_role == user.role]
            return [self._to_trace_response(trace) for trace in rows]

    def create_feedback(self, payload: FeedbackRequest, user: UserProfile) -> FeedbackResponse:
        with db_session() as session:
            feedback = FeedbackModel(
                trace_id=payload.trace_id,
                rating=payload.rating,
                sentiment=payload.sentiment,
                comment=payload.comment,
                created_by=user.username,
            )
            session.add(feedback)
            session.flush()
            return FeedbackResponse(feedback_id=feedback.feedback_id, trace_id=payload.trace_id)

    def list_evaluations(self) -> list[EvaluationRunResponse]:
        runs = self.evaluation_service.list_runs()
        return [self._to_evaluation_response(run) for run in runs]

    def run_evaluation(self, *, name: str, modes: list[str]) -> EvaluationRunResponse:
        run = self.evaluation_service.run_baseline(name=name, modes=modes)
        return self._to_evaluation_response(run)

    def _to_job_response(self, job: JobModel) -> JobResponse:
        return JobResponse(
            job_id=job.job_id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            document_id=job.document_id,
            trace_id=job.trace_id,
            result=job.result,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            finished_at=job.finished_at,
        )

    def _to_trace_response(self, trace: TraceModel) -> TraceResponse:
        return TraceResponse(
            trace_id=trace.trace_id,
            question=trace.question,
            user_role=trace.user_role,
            mode=trace.mode,
            answer=trace.answer,
            plan=trace.plan,
            execution_summary=trace.execution_summary,
            debug=trace.debug,
            citations=trace.citations or [],
            created_at=trace.created_at,
        )

    def _to_evaluation_response(self, run) -> EvaluationRunResponse:
        return EvaluationRunResponse(
            run_id=run.run_id,
            name=run.name,
            status=run.status,
            metrics=run.metrics or {},
            notes=run.notes,
            created_at=run.created_at,
            finished_at=run.finished_at,
        )
