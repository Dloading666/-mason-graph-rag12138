"""Community grouping used by global graph search."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.graphrag_core.models.persistence import CommunityModel, DocumentModel, EntityModel


class CommunityBuilder:
    """Build category and product-centric communities from graph artifacts."""

    def rebuild(self, session: Session) -> int:
        """Recompute all communities from the current graph snapshot."""

        session.execute(delete(CommunityModel))

        documents = session.execute(select(DocumentModel)).scalars().all()
        entities = session.execute(select(EntityModel)).scalars().all()

        grouped_docs: dict[str, list[DocumentModel]] = defaultdict(list)
        for document in documents:
            grouped_docs[document.category].append(document)

        created = 0
        for category, docs in grouped_docs.items():
            entity_names = self._product_names_for_docs(entities, docs)
            session.add(
                CommunityModel(
                    name=f"{category}-community",
                    category="category-community",
                    summary=self._build_category_summary(category, docs, entity_names),
                    source_document_ids=[document.document_id for document in docs],
                    entity_names=entity_names,
                    graph_version=max((document.graph_version for document in docs), default=0),
                )
            )
            created += 1

        for entity in entities:
            if entity.category != "product":
                continue
            docs = [
                document
                for document in documents
                if document.document_id in (entity.source_document_ids or [])
            ]
            if not docs:
                continue
            display_name = next(iter(entity.aliases or [entity.canonical_name]), entity.canonical_name)
            related_entities = self._related_entity_names(entities, docs)
            session.add(
                CommunityModel(
                    name=f"{display_name}-community",
                    category="product-community",
                    summary=self._build_product_summary(display_name, docs, related_entities),
                    source_document_ids=[document.document_id for document in docs],
                    entity_names=related_entities,
                    graph_version=max((document.graph_version for document in docs), default=0),
                )
            )
            created += 1

        return created

    def _product_names_for_docs(self, entities: list[EntityModel], docs: list[DocumentModel]) -> list[str]:
        doc_ids = {document.document_id for document in docs}
        names = [
            next(iter(entity.aliases or [entity.canonical_name]), entity.canonical_name)
            for entity in entities
            if entity.category == "product" and doc_ids.intersection(entity.source_document_ids or [])
        ]
        return sorted(set(names))

    def _related_entity_names(self, entities: list[EntityModel], docs: list[DocumentModel]) -> list[str]:
        doc_ids = {document.document_id for document in docs}
        names = [
            next(iter(entity.aliases or [entity.canonical_name]), entity.canonical_name)
            for entity in entities
            if doc_ids.intersection(entity.source_document_ids or [])
        ]
        return sorted(set(names))

    def _build_category_summary(self, category: str, documents: list[DocumentModel], entity_names: list[str]) -> str:
        titles = " / ".join(document.title for document in documents[:4])
        entity_text = "、".join(entity_names[:6]) or "暂无实体摘要"
        return f"{category}主题社区，覆盖文档：{titles}。核心产品或实体：{entity_text}。"

    def _build_product_summary(self, product_name: str, documents: list[DocumentModel], entity_names: list[str]) -> str:
        categories = "、".join(sorted({document.category for document in documents}))
        sources = " / ".join(document.source for document in documents[:4])
        related = "、".join(entity_names[:8]) or "暂无关联实体"
        return (
            f"{product_name}产品社区，覆盖分类：{categories}。"
            f"关键来源：{sources}。"
            f"关联实体：{related}。"
        )
