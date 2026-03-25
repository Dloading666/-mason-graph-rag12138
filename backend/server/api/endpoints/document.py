"""Document management and knowledge-base governance endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.core.contracts import (
    ChunkPreviewRequest,
    ChunkPreviewResponse,
    DocumentSummary,
    IngestResponse,
    KnowledgeBaseSettings,
    RetrievalTestRequest,
    RetrievalTestResponse,
    UserProfile,
)
from backend.server.api.dependencies import get_current_user
from backend.server.services.document_service import DocumentService


router = APIRouter()


@router.get("", response_model=list[DocumentSummary])
def list_documents(user: UserProfile = Depends(get_current_user)) -> list[DocumentSummary]:
    service = DocumentService()
    return service.list_documents(user.role)


@router.get("/settings", response_model=KnowledgeBaseSettings)
def get_knowledge_base_settings(user: UserProfile = Depends(get_current_user)) -> KnowledgeBaseSettings:
    service = DocumentService()
    return service.get_settings()


@router.put("/settings", response_model=KnowledgeBaseSettings)
def update_knowledge_base_settings(
    payload: KnowledgeBaseSettings,
    user: UserProfile = Depends(get_current_user),
) -> KnowledgeBaseSettings:
    if user.role not in {"admin", "purchase"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前角色无权修改知识库设置")

    service = DocumentService()
    try:
        return service.update_settings(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/retrieval-test", response_model=RetrievalTestResponse)
def run_retrieval_test(
    payload: RetrievalTestRequest,
    user: UserProfile = Depends(get_current_user),
) -> RetrievalTestResponse:
    service = DocumentService()
    try:
        return service.run_retrieval_test(payload, user.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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


@router.post("/{document_id}/chunk-preview", response_model=ChunkPreviewResponse)
def preview_document_chunks(
    document_id: str,
    payload: ChunkPreviewRequest,
    user: UserProfile = Depends(get_current_user),
) -> ChunkPreviewResponse:
    service = DocumentService()
    try:
        settings_override = None
        if payload.chunking is not None:
            settings_override = service.get_settings().model_copy(update={"chunking": payload.chunking})
        return service.preview_chunks(
            document_id,
            user_role=user.role,
            settings_override=settings_override,
            limit=payload.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


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
