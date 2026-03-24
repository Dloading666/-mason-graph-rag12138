"""Read-only graph query service backed by persisted graph artifacts."""

from __future__ import annotations

from sqlalchemy import select

from backend.core.contracts import GraphCommunity, GraphEdge, GraphNode, GraphResponse
from backend.graphrag_core.db.session import db_session
from backend.graphrag_core.integrations.neo4j_store import Neo4jGraphStore
from backend.graphrag_core.models.persistence import CommunityModel, EntityModel, MentionModel, RelationModel
from backend.graphrag_core.runtime import bootstrap_runtime
from backend.server.services.document_service import DocumentService


class GraphService:
    """Build a graph snapshot from persisted documents and entities."""

    def __init__(self) -> None:
        bootstrap_runtime()
        self.document_service = DocumentService()
        self.neo4j = Neo4jGraphStore()

    def get_graph(self, user_role: str) -> GraphResponse:
        self.document_service.ensure_ready_documents(user_role)
        with db_session() as session:
            documents = self.document_service._visible_documents(session, user_role)
            visible_pk = {document.pk for document in documents}
            visible_document_ids = {document.document_id for document in documents}

            if self.neo4j.enabled:
                snapshot = self.neo4j.graph_snapshot(visible_document_ids=visible_document_ids)
                if snapshot:
                    return self._build_from_neo4j(snapshot)

            mentions = [
                mention
                for mention in session.execute(select(MentionModel)).scalars().all()
                if mention.document_pk in visible_pk
            ]
            entity_ids = {mention.entity_pk for mention in mentions}
            entities = {
                entity.pk: entity
                for entity in session.execute(select(EntityModel)).scalars().all()
                if entity.pk in entity_ids
            }
            relations = [
                relation
                for relation in session.execute(select(RelationModel)).scalars().all()
                if relation.document_pk in visible_pk
            ]
            communities = [
                community
                for community in session.execute(select(CommunityModel)).scalars().all()
                if set(community.source_document_ids or []).intersection(visible_document_ids)
            ]
            return self._build_from_sql(documents, mentions, entities, relations, communities)

    def _build_from_neo4j(self, snapshot: dict[str, object]) -> GraphResponse:
        document_rows = snapshot["documents"]
        relation_rows = snapshot["relations"]
        community_rows = snapshot["communities"]

        nodes: list[GraphNode] = []
        source_documents: set[str] = set()
        entity_neighbors: dict[str, list[str]] = {}
        seen_entities: set[str] = set()

        for document in document_rows:
            nodes.append(
                GraphNode(
                    id=f"doc:{document['document_id']}",
                    name=document["title"],
                    category=document["category"],
                    source_documents=[document["source"]],
                )
            )
            source_documents.add(document["source"])
            for entity in document.get("entities", []):
                if not entity or not entity.get("entity_id") or entity["entity_id"] in seen_entities:
                    continue
                seen_entities.add(entity["entity_id"])
                nodes.append(
                    GraphNode(
                        id=f"entity:{entity['entity_id']}",
                        name=entity["name"],
                        category=entity["category"],
                        source_documents=[document["source"]],
                    )
                )

        edges: list[GraphEdge] = []
        for document in document_rows:
            for entity in document.get("entities", []):
                if not entity or not entity.get("entity_id"):
                    continue
                edges.append(
                    GraphEdge(
                        source=f"doc:{document['document_id']}",
                        target=f"entity:{entity['entity_id']}",
                        relation="mentions",
                    )
                )

        for relation in relation_rows:
            edges.append(
                GraphEdge(
                    source=f"entity:{relation['source_entity_id']}",
                    target=f"entity:{relation['target_entity_id']}",
                    relation=str(relation["relation"]).lower(),
                    weight=float(relation.get("confidence") or 1.0),
                )
            )
            entity_neighbors.setdefault(relation["source_name"], [])
            if relation["target_name"] not in entity_neighbors[relation["source_name"]]:
                entity_neighbors[relation["source_name"]].append(relation["target_name"])

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            communities=[
                GraphCommunity(
                    community_id=item["community_id"],
                    name=item["name"],
                    category=item["category"],
                    summary=item["summary"],
                    source_documents=item.get("source_document_ids", []),
                    entity_names=item.get("entity_names", []),
                )
                for item in community_rows
            ],
            source_documents=sorted(source_documents),
            entity_neighbors=entity_neighbors,
        )

    def _build_from_sql(self, documents, mentions, entities, relations, communities) -> GraphResponse:
        nodes = [
            GraphNode(
                id=f"doc:{document.document_id}",
                name=document.title,
                category=document.category,
                source_documents=[document.source],
            )
            for document in documents
        ]
        for entity in entities.values():
            nodes.append(
                GraphNode(
                    id=f"entity:{entity.entity_id}",
                    name=next(iter(entity.aliases or [entity.canonical_name]), entity.canonical_name),
                    category=entity.category,
                    source_documents=entity.source_document_ids or [],
                )
            )

        edges = []
        for mention in mentions:
            entity = entities.get(mention.entity_pk)
            document = next((item for item in documents if item.pk == mention.document_pk), None)
            if entity is None or document is None:
                continue
            edges.append(
                GraphEdge(
                    source=f"doc:{document.document_id}",
                    target=f"entity:{entity.entity_id}",
                    relation="mentions",
                )
            )
        for relation in relations:
            if relation.source_entity_pk not in entities or relation.target_entity_pk not in entities:
                continue
            edges.append(
                GraphEdge(
                    source=f"entity:{entities[relation.source_entity_pk].entity_id}",
                    target=f"entity:{entities[relation.target_entity_pk].entity_id}",
                    relation=relation.relation_type,
                    weight=relation.confidence,
                )
            )

        neighbor_map: dict[str, list[str]] = {}
        for relation in relations:
            source_entity = entities.get(relation.source_entity_pk)
            target_entity = entities.get(relation.target_entity_pk)
            if source_entity is None or target_entity is None:
                continue
            source_name = next(iter(source_entity.aliases or [source_entity.canonical_name]), source_entity.canonical_name)
            target_name = next(iter(target_entity.aliases or [target_entity.canonical_name]), target_entity.canonical_name)
            neighbor_map.setdefault(source_name, [])
            if target_name not in neighbor_map[source_name]:
                neighbor_map[source_name].append(target_name)

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            communities=[
                GraphCommunity(
                    community_id=community.community_id,
                    name=community.name,
                    category=community.category,
                    summary=community.summary,
                    source_documents=community.source_document_ids or [],
                    entity_names=community.entity_names or [],
                )
                for community in communities
            ],
            source_documents=sorted({document.source for document in documents}),
            entity_neighbors=neighbor_map,
        )
