"""Multi-mode retrieval across chunks, graph entities, communities, and short paths."""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import sqrt

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.evidence import EvidenceItem
from backend.embedding.ali_embedding import AliTextEmbedding
from backend.graphrag_core.integrations.neo4j_store import Neo4jGraphStore
from backend.graphrag_core.models.persistence import ChunkModel, CommunityModel, DocumentModel, EntityModel, MentionModel


QUESTION_COMPLEXITY_MARKERS = ("对比", "方案", "流程", "报告", "总结", "为什么", "风险", "建议")


@dataclass
class RetrievalResult:
    """Structured retrieval result returned to the QA layer."""

    mode: str
    evidence: list[EvidenceItem]
    debug: dict[str, object]


class MultiModeSearchService:
    """Support naive, local, global, and hybrid retrieval modes."""

    def __init__(self) -> None:
        self.embedder = AliTextEmbedding()
        self.neo4j = Neo4jGraphStore()

    def search(
        self,
        session: Session,
        *,
        question: str,
        user_role: str,
        requested_mode: str = "auto",
        limit: int = 6,
    ) -> RetrievalResult:
        """Route the query to a retrieval strategy and return ranked evidence."""

        mode = self._resolve_mode(question, requested_mode)
        if mode == "naive":
            evidence, debug = self._naive_search(session, question, user_role, limit)
        elif mode == "local":
            evidence, debug = self._local_graph_search(session, question, user_role, limit)
        elif mode == "global":
            evidence, debug = self._global_search(session, question, user_role, limit)
        else:
            evidence, debug = self._hybrid_search(session, question, user_role, limit)
            mode = "hybrid" if mode == "auto" else mode
        return RetrievalResult(mode=mode, evidence=evidence, debug=debug)

    def _resolve_mode(self, question: str, requested_mode: str) -> str:
        if requested_mode and requested_mode != "auto":
            return requested_mode
        if any(marker in question for marker in QUESTION_COMPLEXITY_MARKERS) or len(question) >= 28:
            return "hybrid"
        return "naive"

    def _visible_documents(self, session: Session, user_role: str) -> list[DocumentModel]:
        documents = session.execute(select(DocumentModel)).scalars().all()
        if user_role == "admin":
            return documents
        return [document for document in documents if user_role in (document.allowed_roles or [])]

    def _naive_search(
        self, session: Session, question: str, user_role: str, limit: int
    ) -> tuple[list[EvidenceItem], dict[str, object]]:
        visible_docs = self._visible_documents(session, user_role)
        visible_doc_ids = {document.pk for document in visible_docs}
        if not visible_doc_ids:
            return [], {"documents": 0, "chunks": 0, "source": "sql"}

        query_terms = self._build_query_terms(question)
        query_embedding = self.embedder.safe_embed_text(question, text_type="query")
        chunk_rows = [
            chunk
            for chunk in session.execute(select(ChunkModel)).scalars().all()
            if chunk.document_pk in visible_doc_ids
        ]

        ranked: list[tuple[float, ChunkModel, DocumentModel]] = []
        doc_by_pk = {document.pk: document for document in visible_docs}
        for chunk in chunk_rows:
            keyword_score = sum(1 for term in query_terms if term in chunk.content.lower())
            if question[:8] and question[:8] in chunk.content:
                keyword_score += 2
            semantic_score = self._cosine_similarity(query_embedding, chunk.embedding)
            score = keyword_score * 0.55 + semantic_score * 0.45
            if score <= 0:
                continue
            ranked.append((score, chunk, doc_by_pk[chunk.document_pk]))

        ranked.sort(key=lambda item: item[0], reverse=True)
        evidence = [
            EvidenceItem(
                title=document.title,
                source=document.source,
                snippet=chunk.content[:240],
                citation=chunk.citation,
                score=round(score, 4),
            )
            for score, chunk, document in ranked[:limit]
        ]
        return evidence, {"documents": len(visible_docs), "chunks": len(chunk_rows), "source": "sql"}

    def _local_graph_search(
        self, session: Session, question: str, user_role: str, limit: int
    ) -> tuple[list[EvidenceItem], dict[str, object]]:
        visible_docs = self._visible_documents(session, user_role)
        visible_doc_ids = {document.pk for document in visible_docs}
        visible_document_ids = {document.document_id for document in visible_docs}
        visible_doc_lookup = {document.pk: document for document in visible_docs}
        query_terms = self._build_query_terms(question)

        if self.neo4j.enabled:
            local_rows = self.neo4j.local_search(
                query_terms=query_terms,
                visible_document_ids=visible_document_ids,
                limit=limit,
            )
            path_rows = self.neo4j.path_search(
                query_terms=query_terms,
                visible_document_ids=visible_document_ids,
                limit=max(2, limit // 2),
            )
            evidence: list[EvidenceItem] = []
            for row in local_rows:
                evidence.append(
                    EvidenceItem(
                        title=row["title"],
                        source=row["source"],
                        snippet=self._compose_local_snippet(
                            row.get("entity_name", ""),
                            row.get("category", ""),
                            row.get("neighbors", []),
                            row.get("relations", []),
                        ),
                        citation=f"{row['source']}#neo4j-local",
                        score=round(0.8 + min(float(row.get("degree", 0)) * 0.02, 0.15), 4),
                    )
                )
            for row in path_rows:
                evidence.append(
                    EvidenceItem(
                        title=row["title"],
                        source=row["source"],
                        snippet=self._compose_path_snippet(
                            row.get("source_name", ""),
                            row.get("target_name", ""),
                            row.get("path_nodes", []),
                            row.get("path_relations", []),
                        ),
                        citation=f"{row['source']}#neo4j-path",
                        score=round(0.83 - min(float(row.get("hop_count", 1)) * 0.03, 0.06), 4),
                    )
                )
            if evidence:
                deduped = self._dedupe_evidence(evidence, limit)
                return deduped, {
                    "documents": len(visible_docs),
                    "entity_hits": len(local_rows),
                    "path_hits": len(path_rows),
                    "source": "neo4j",
                }

        mentions = session.execute(select(MentionModel)).scalars().all()
        chunks = {chunk.pk: chunk for chunk in session.execute(select(ChunkModel)).scalars().all()}
        entities = {entity.pk: entity for entity in session.execute(select(EntityModel)).scalars().all()}

        ranked: list[tuple[float, EvidenceItem]] = []
        for mention in mentions:
            if mention.document_pk not in visible_doc_ids:
                continue
            entity = entities.get(mention.entity_pk)
            if entity is None:
                continue
            aliases = set(entity.aliases or [])
            if not any(term in alias.lower() for term in query_terms for alias in aliases):
                if not any(alias in question for alias in aliases):
                    continue
            document = visible_doc_lookup[mention.document_pk]
            chunk = chunks.get(mention.chunk_pk)
            snippet = chunk.content[:240] if chunk is not None else document.content[:240]
            citation = chunk.citation if chunk is not None else document.source
            score = mention.confidence + 0.1 * len(aliases)
            ranked.append(
                (
                    score,
                    EvidenceItem(
                        title=document.title,
                        source=document.source,
                        snippet=snippet,
                        citation=citation,
                        score=round(score, 4),
                    ),
                )
            )

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked[:limit]], {"documents": len(visible_docs), "mentions": len(ranked), "source": "sql"}

    def _global_search(
        self, session: Session, question: str, user_role: str, limit: int
    ) -> tuple[list[EvidenceItem], dict[str, object]]:
        visible_docs = self._visible_documents(session, user_role)
        visible_document_ids = {document.document_id for document in visible_docs}
        query_terms = self._build_query_terms(question)

        communities = session.execute(select(CommunityModel)).scalars().all()

        if self.neo4j.enabled:
            if communities and not self.neo4j.has_label("Community"):
                self.neo4j.sync_communities(communities)
            community_rows = self.neo4j.global_search(
                query_terms=query_terms,
                visible_document_ids=visible_document_ids,
                limit=limit,
            )
            if community_rows:
                evidence = [
                    EvidenceItem(
                        title=row["name"],
                        source="neo4j-community",
                        snippet=self._compose_community_snippet(
                            row["summary"],
                            row.get("entity_names", []),
                            row.get("category", ""),
                        ),
                        citation=row["community_id"],
                        score=round(0.75 + min(float(row.get("entity_count", 0)) * 0.01, 0.18), 4),
                    )
                    for row in community_rows
                ]
                return evidence, {"communities": len(community_rows), "source": "neo4j"}

        ranked: list[tuple[float, EvidenceItem]] = []
        for community in communities:
            if visible_document_ids and not set(community.source_document_ids or []).intersection(visible_document_ids):
                continue
            haystack = " ".join([community.name, community.summary, " ".join(community.entity_names or [])]).lower()
            matches = sum(1 for term in query_terms if term in haystack)
            if matches <= 0:
                continue
            score = float(matches)
            ranked.append(
                (
                    score,
                    EvidenceItem(
                        title=community.name,
                        source="community-summary",
                        snippet=community.summary[:240],
                        citation=community.community_id,
                        score=round(score, 4),
                    ),
                )
            )

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked[:limit]], {"communities": len(communities), "source": "sql"}

    def _hybrid_search(
        self, session: Session, question: str, user_role: str, limit: int
    ) -> tuple[list[EvidenceItem], dict[str, object]]:
        naive, naive_debug = self._naive_search(session, question, user_role, limit)
        local, local_debug = self._local_graph_search(session, question, user_role, limit)
        global_items, global_debug = self._global_search(session, question, user_role, limit)

        merged: dict[str, EvidenceItem] = {}
        for weight, evidence_list in ((1.0, naive), (0.98, local), (0.78, global_items)):
            for item in evidence_list:
                boosted = item.model_copy(update={"score": round(item.score * weight, 4)})
                current = merged.get(boosted.citation)
                if current is None or boosted.score > current.score:
                    merged[boosted.citation] = boosted

        ranked = sorted(merged.values(), key=lambda item: item.score, reverse=True)[:limit]
        return ranked, {
            "naive": naive_debug,
            "local": local_debug,
            "global": global_debug,
            "merged_results": len(ranked),
            "source": "mixed",
        }

    def _build_query_terms(self, question: str) -> set[str]:
        lowered = question.lower().strip()
        if not lowered:
            return set()

        terms: set[str] = set()
        for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9\.-]+", lowered):
            cleaned = token.strip()
            if not cleaned:
                continue
            terms.add(cleaned)
            if re.fullmatch(r"[\u4e00-\u9fff]+", cleaned):
                for size in range(2, min(5, len(cleaned) + 1)):
                    for start in range(0, len(cleaned) - size + 1):
                        terms.add(cleaned[start : start + size])
        return {term for term in terms if len(term) >= 2}

    def _cosine_similarity(self, left: np.ndarray | None, right: list[float] | None) -> float:
        if left is None or right is None:
            return 0.0
        right_array = np.asarray(right, dtype=np.float32)
        numerator = float(np.dot(left, right_array))
        denominator = sqrt(float(np.dot(left, left))) * sqrt(float(np.dot(right_array, right_array)))
        if not denominator:
            return 0.0
        return numerator / denominator

    def _compose_local_snippet(
        self,
        entity_name: str,
        category: str,
        neighbors: list[str] | None,
        relations: list[str] | None,
    ) -> str:
        neighbor_text = "、".join(neighbors or []) or "无邻居实体"
        relation_text = "、".join(relations or []) or "无关系类型"
        return f"命中实体：{entity_name}（{category}）。关联实体：{neighbor_text}。关系类型：{relation_text}。"

    def _compose_path_snippet(
        self,
        source_name: str,
        target_name: str,
        path_nodes: list[str] | None,
        path_relations: list[str] | None,
    ) -> str:
        nodes = " -> ".join(path_nodes or []) or "未返回路径节点"
        relations = "、".join(path_relations or []) or "未返回路径关系"
        return f"路径推理：{source_name} 与 {target_name} 的关联路径为 {nodes}。涉及关系：{relations}。"

    def _compose_community_snippet(self, summary: str, entity_names: list[str] | None, category: str) -> str:
        entities = "、".join((entity_names or [])[:6]) or "暂无实体"
        return f"{summary[:180]} 该社区类型：{category}。核心实体：{entities}。"

    def _dedupe_evidence(self, evidence: list[EvidenceItem], limit: int) -> list[EvidenceItem]:
        merged: dict[str, EvidenceItem] = {}
        for item in evidence:
            current = merged.get(item.citation)
            if current is None or item.score > current.score:
                merged[item.citation] = item
        return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:limit]
