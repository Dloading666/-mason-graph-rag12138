"""QA endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.core.contracts import QaRequest, QaResponse, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.qa_service import QaService


router = APIRouter()


@router.post("/ask", response_model=QaResponse)
def ask_question(payload: QaRequest, user: UserProfile = Depends(get_current_user)) -> QaResponse:
    service = QaService()
    return service.ask(payload, user.role)


@router.post("/ask-stream")
def ask_question_stream(payload: QaRequest, user: UserProfile = Depends(get_current_user)) -> StreamingResponse:
    service = QaService()

    def event_stream():
        yield "event: stage\ndata: {\"stage\":\"retrieving\"}\n\n"
        response = service.ask(payload, user.role)
        yield f"event: answer\ndata: {json.dumps(response.model_dump(mode='json'), ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {\"status\":\"completed\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
