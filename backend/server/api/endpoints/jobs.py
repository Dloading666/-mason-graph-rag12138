"""Async job endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.core.contracts import JobResponse, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.platform_service import PlatformService


router = APIRouter()


@router.get("", response_model=list[JobResponse])
def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    user: UserProfile = Depends(get_current_user),
) -> list[JobResponse]:
    service = PlatformService()
    return service.list_jobs(user=user, limit=limit)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, user: UserProfile = Depends(get_current_user)) -> JobResponse:
    service = PlatformService()
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
