"""Graph query endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.contracts import GraphResponse, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.graph_service import GraphService


router = APIRouter()


@router.get("", response_model=GraphResponse)
def get_graph(user: UserProfile = Depends(get_current_user)) -> GraphResponse:
    service = GraphService()
    return service.get_graph(user.role)
