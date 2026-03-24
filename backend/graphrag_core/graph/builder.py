"""Entity extraction, alignment, and relation building."""

from __future__ import annotations

import re
from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.graphrag_core.models.persistence import (
    ChunkModel,
    DocumentModel,
    EntityModel,
    MentionModel,
    RelationModel,
)


STANDARD_PATTERN = re.compile(r"(?:GB|JGJ)\s?\d+(?:\.\d+)?(?:-\d{4})?")
PRODUCT_KEYWORDS = [
    "抗裂砂浆",
    "保温砂浆",
    "外墙保温系统",
    "瓷砖胶",
    "水泥",
    "砂石",
    "JS防水涂料",
    "石膏基自流平",
]
PROCESS_KEYWORDS = [
    "施工",
    "验收",
    "搅拌",
    "铺贴",
    "基层处理",
    "闭水试验",
    "采购",
    "审批",
    "养护",
]
MATERIAL_KEYWORDS = [
    "砂石",
    "水泥",
    "网格布",
    "锚栓",
]


def normalize_entity_name(name: str) -> str:
    """Normalize entity text for alignment."""

    return re.sub(r"\s+", "", name).lower()


class GraphBuilder:
    """Build canonical entities, mentions, and relations for one document."""

    def rebuild_document_graph(self, session: Session, document: DocumentModel, chunks: Iterable[ChunkModel]) -> dict[str, int]:
        """Rebuild graph artifacts for a single document."""

        session.execute(delete(RelationModel).where(RelationModel.document_pk == document.pk))
        session.execute(delete(MentionModel).where(MentionModel.document_pk == document.pk))

        extracted = self._extract_entities(document)
        entity_records: dict[str, EntityModel] = {}
        mention_count = 0

        for name, category in extracted:
            normalized = normalize_entity_name(name)
            entity = session.execute(
                select(EntityModel).where(
                    EntityModel.canonical_name == normalized,
                    EntityModel.category == category,
                )
            ).scalar_one_or_none()
            if entity is None:
                entity = EntityModel(
                    canonical_name=normalized,
                    category=category,
                    aliases=[name],
                    source_document_ids=[document.document_id],
                )
                session.add(entity)
                session.flush()
            else:
                aliases = set(entity.aliases or [])
                aliases.add(name)
                entity.aliases = sorted(aliases)
                sources = set(entity.source_document_ids or [])
                sources.add(document.document_id)
                entity.source_document_ids = sorted(sources)

            entity_records[f"{category}:{normalized}"] = entity
            chunk = self._match_chunk(name, chunks)
            session.add(
                MentionModel(
                    document_pk=document.pk,
                    chunk_pk=chunk.pk if chunk else None,
                    entity_pk=entity.pk,
                    mention_text=name,
                    normalized_text=normalized,
                )
            )
            mention_count += 1

        relation_count = self._create_relations(session, document, entity_records)
        return {
            "entities": len(entity_records),
            "mentions": mention_count,
            "relations": relation_count,
        }

    def _extract_entities(self, document: DocumentModel) -> list[tuple[str, str]]:
        text = f"{document.title}\n{document.content}"
        found: list[tuple[str, str]] = []

        for standard in STANDARD_PATTERN.findall(text):
            found.append((standard.replace(" ", ""), "compliance"))
        for keyword in PRODUCT_KEYWORDS:
            if keyword in text:
                found.append((keyword, "product"))
        for keyword in PROCESS_KEYWORDS:
            if keyword in text:
                found.append((keyword, "process"))
        for keyword in MATERIAL_KEYWORDS:
            if keyword in text:
                found.append((keyword, "material"))

        seen: set[str] = set()
        deduped: list[tuple[str, str]] = []
        for name, category in found:
            marker = f"{category}:{normalize_entity_name(name)}"
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append((name, category))
        return deduped

    def _match_chunk(self, entity_name: str, chunks: Iterable[ChunkModel]) -> ChunkModel | None:
        for chunk in chunks:
            if entity_name in chunk.content:
                return chunk
        return next(iter(chunks), None)

    def _create_relations(
        self,
        session: Session,
        document: DocumentModel,
        entity_records: dict[str, EntityModel],
    ) -> int:
        products = [entity for key, entity in entity_records.items() if key.startswith("product:")]
        materials = [entity for key, entity in entity_records.items() if key.startswith("material:")]
        processes = [entity for key, entity in entity_records.items() if key.startswith("process:")]
        compliance_items = [entity for key, entity in entity_records.items() if key.startswith("compliance:")]

        relations: list[tuple[EntityModel, EntityModel, str]] = []
        for product in products:
            for material in materials:
                relations.append((product, material, "related_to"))
            for process in processes:
                relations.append((product, process, "applies_to"))
            for compliance in compliance_items:
                relations.append((product, compliance, "complies_with"))
        for process in processes:
            for compliance in compliance_items:
                relations.append((process, compliance, "complies_with"))

        created = 0
        for source, target, relation_type in relations:
            exists = session.execute(
                select(RelationModel).where(
                    RelationModel.document_pk == document.pk,
                    RelationModel.source_entity_pk == source.pk,
                    RelationModel.target_entity_pk == target.pk,
                    RelationModel.relation_type == relation_type,
                )
            ).scalar_one_or_none()
            if exists is not None:
                continue
            session.add(
                RelationModel(
                    document_pk=document.pk,
                    source_entity_pk=source.pk,
                    target_entity_pk=target.pk,
                    relation_type=relation_type,
                    confidence=0.72,
                )
            )
            created += 1
        return created
