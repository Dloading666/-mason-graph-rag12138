"""Trace lookup endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.core.contracts import TraceResponse, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.platform_service import PlatformService


router = APIRouter()


@router.get("", response_model=list[TraceResponse])
def list_traces(
    limit: int = Query(default=50, ge=1, le=200),
    user: UserProfile = Depends(get_current_user),
) -> list[TraceResponse]:
    service = PlatformService()
    return service.list_traces(user=user, limit=limit)


@router.get("/{trace_id}", response_model=TraceResponse)
def get_trace(trace_id: str, user: UserProfile = Depends(get_current_user)) -> TraceResponse:
    service = PlatformService()
    trace = service.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    if user.role != "admin" and trace.user_role != user.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前角色无权查看该追踪记录")
    return trace
