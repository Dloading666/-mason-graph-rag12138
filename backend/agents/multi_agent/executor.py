"""Execution agent scaffold."""

from __future__ import annotations

from backend.core.evidence import EvidenceItem
from backend.search.tool.hybrid_search import HybridSearch
from backend.server.services.document_service import DocumentService


class ExecutorAgent:
    def __init__(self) -> None:
        self.search = HybridSearch()
        self.documents = DocumentService()

    def run(self, question: str, user_role: str) -> list[EvidenceItem]:
        docs = self.documents.list_full_documents(user_role)
        return self.search.search(question, docs)

