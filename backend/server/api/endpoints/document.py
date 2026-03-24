"""Document management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.core.contracts import DocumentSummary, IngestResponse, UserProfile
from backend.server.api.dependencies import get_current_user
from backend.server.services.document_service import DocumentService


router = APIRouter()


@router.get("", response_model=list[DocumentSummary])
def list_documents(user: UserProfile = Depends(get_current_user)) -> list[DocumentSummary]:
    service = DocumentService()
    return service.list_documents(user.role)


@router.post("/upload", response_model=DocumentSummary, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("general"),
    allowed_roles: str = Form("normal,purchase,admin"),
    user: UserProfile = Depends(get_current_user),
) -> DocumentSummary:
    if user.role not in {"admin", "purchase"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前角色无上传权限")

    service = DocumentService()
    parsed_roles = [item.strip() for item in allowed_roles.split(",") if item.strip()]
    try:
        return await service.save_upload(file, category=category, allowed_roles=parsed_roles)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{document_id}/ingest", response_model=IngestResponse)
def ingest_document(document_id: str, user: UserProfile = Depends(get_current_user)) -> IngestResponse:
    if user.role not in {"admin", "purchase"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前角色无入库权限")

    service = DocumentService()
    try:
        return service.ingest_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, user: UserProfile = Depends(get_current_user)) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可删除文档")

    service = DocumentService()
    try:
        service.delete_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
