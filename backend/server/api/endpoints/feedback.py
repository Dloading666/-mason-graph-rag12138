"""Feedback endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.contracts import FeedbackRequest, FeedbackResponse, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.platform_service import PlatformService


router = APIRouter()


@router.post("", response_model=FeedbackResponse)
def create_feedback(payload: FeedbackRequest, user: UserProfile = Depends(get_current_user)) -> FeedbackResponse:
    service = PlatformService()
    return service.create_feedback(payload, user)
