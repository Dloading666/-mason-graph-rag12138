"""Persistence helpers for QA traces."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.graphrag_core.models.persistence import TraceModel


class TraceStore:
    """Create and fetch persisted execution traces."""

    def record_trace(
        self,
        session: Session,
        *,
        trace_id: str,
        question: str,
        user_role: str,
        mode: str,
        answer: str,
        plan: dict | None,
        execution_summary: dict | None,
        debug: dict | None,
        citations: list[str],
    ) -> TraceModel:
        trace = TraceModel(
            trace_id=trace_id,
            question=question,
            user_role=user_role,
            mode=mode,
            answer=answer,
            plan=plan,
            execution_summary=execution_summary,
            debug=debug,
            citations=citations,
        )
        session.add(trace)
        session.flush()
        return trace

    def get_trace(self, session: Session, trace_id: str) -> TraceModel | None:
        return session.execute(select(TraceModel).where(TraceModel.trace_id == trace_id)).scalar_one_or_none()
