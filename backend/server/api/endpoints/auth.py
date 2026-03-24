"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.core.contracts import LoginRequest, LoginResponse
from backend.server.services.auth_service import AuthService


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    service = AuthService()
    try:
        return service.login(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

