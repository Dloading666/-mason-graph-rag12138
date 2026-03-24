"""Runtime bootstrap for the GraphRAG core services."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import select

from backend.config.settings import settings
from backend.graphrag_core.db.session import db_session, init_db
from backend.graphrag_core.integrations.object_storage import ObjectStorageService
from backend.graphrag_core.models.persistence import DocumentModel


def bootstrap_runtime() -> None:
    """Prepare directories, tables, buckets, and initial seed documents."""

    settings.document_storage_dir.mkdir(parents=True, exist_ok=True)
    settings.document_index_file.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    storage = ObjectStorageService()
    storage.ensure_bucket()
    sync_seed_documents()


def sync_seed_documents() -> None:
    """Import seed documents from the development JSON index when missing."""

    if not settings.document_index_file.exists():
        return

    try:
        payload = json.loads(settings.document_index_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse document seed file {}: {}", settings.document_index_file, exc)
        return

    if not isinstance(payload, list):
        return

    with db_session() as session:
        existing_ids = {
            row[0]
            for row in session.execute(select(DocumentModel.document_id)).all()
        }
        for item in payload:
            document_id = item.get("document_id")
            if not document_id or document_id in existing_ids:
                continue

            updated_at = item.get("updated_at")
            try:
                parsed_updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00")) if updated_at else None
            except (TypeError, ValueError):
                parsed_updated_at = None

            model = DocumentModel(
                document_id=document_id,
                title=item.get("title") or "Untitled document",
                source=item.get("source") or document_id,
                category=item.get("category") or "general",
                content=item.get("content") or "",
                allowed_roles=item.get("allowed_roles") or ["normal", "purchase", "admin"],
                status=item.get("status") or "indexed",
                ingestion_status="indexed" if item.get("status") == "indexed" else "pending",
                version=int(item.get("version") or 1),
                graph_version=1 if item.get("status") == "indexed" else 0,
                index_version=1 if item.get("status") == "indexed" else 0,
                processing_errors=[],
                created_at=parsed_updated_at or datetime.now(UTC),
                updated_at=parsed_updated_at or datetime.now(UTC),
            )
            session.add(model)
