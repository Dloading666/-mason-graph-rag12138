"""Research and background report endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.contracts import ResearchJobResponse, ResearchRequest, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.platform_service import PlatformService


router = APIRouter()


@router.post("/report", response_model=ResearchJobResponse)
def create_report(payload: ResearchRequest, user: UserProfile = Depends(get_current_user)) -> ResearchJobResponse:
    service = PlatformService()
    return service.create_research_job(question=payload.question, mode=payload.mode, user=user)
