"""Evaluation run access and execution layer."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from backend.graphrag_core.db.session import db_session
from backend.graphrag_core.evaluation.runner import EvaluationRunner
from backend.graphrag_core.models.persistence import EvaluationRunModel
from backend.server.services.document_service import DocumentService


class EvaluationService:
    """List and execute persisted evaluation runs."""

    def __init__(self) -> None:
        self.runner = EvaluationRunner()

    def list_runs(self) -> list[EvaluationRunModel]:
        with db_session() as session:
            return session.execute(
                select(EvaluationRunModel).order_by(EvaluationRunModel.created_at.desc())
            ).scalars().all()

    def run_baseline(self, *, name: str, modes: list[str]) -> EvaluationRunModel:
        DocumentService().ensure_ready_documents("admin")
        with db_session() as session:
            run = EvaluationRunModel(
                name=name,
                status="queued",
                metrics={"requested_modes": modes},
            )
            session.add(run)
            session.flush()
            try:
                self.runner.run(session, run, modes)
                run.finished_at = datetime.now(UTC)
            except Exception as exc:
                run.status = "failed"
                run.notes = str(exc)
                run.finished_at = datetime.now(UTC)
                raise
            return run
