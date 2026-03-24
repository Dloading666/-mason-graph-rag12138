"""Evaluation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.contracts import EvaluationRunRequest, EvaluationRunResponse, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.platform_service import PlatformService


router = APIRouter()


@router.get("/runs", response_model=list[EvaluationRunResponse])
def list_runs(user: UserProfile = Depends(get_current_user)) -> list[EvaluationRunResponse]:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可查看评估结果")
    service = PlatformService()
    return service.list_evaluations()


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(payload: EvaluationRunRequest, user: UserProfile = Depends(get_current_user)) -> EvaluationRunResponse:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可运行评估")
    service = PlatformService()
    return service.run_evaluation(name=payload.name, modes=payload.modes)
