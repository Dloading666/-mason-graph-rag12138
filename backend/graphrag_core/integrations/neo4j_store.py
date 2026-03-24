"""Optional Neo4j synchronization and query helpers for graph artifacts."""

from __future__ import annotations

from collections.abc import Iterable

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.graphrag_core.models.persistence import CommunityModel, DocumentModel, EntityModel, MentionModel, RelationModel


class Neo4jGraphStore:
    """Mirror and query graph artifacts in Neo4j when enabled."""

    def __init__(self) -> None:
        self._driver = None
        self._labels_cache: set[str] | None = None
        if not settings.NEO4J_ENABLED:
            return
        try:
            from neo4j import GraphDatabase
        except ImportError:
            logger.warning("neo4j driver is not installed; skipping graph synchronization.")
            return
        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    @property
    def enabled(self) -> bool:
        return self._driver is not None

    def has_label(self, label: str) -> bool:
        """Check whether a node label exists before running label-specific queries."""

        if not self.enabled:
            return False

        if self._labels_cache is None:
            try:
                with self._driver.session() as neo4j_session:
                    result = neo4j_session.run("CALL db.labels() YIELD label RETURN collect(label) AS labels")
                    record = result.single()
                    self._labels_cache = set(record["labels"] if record is not None else [])
            except Exception as exc:
                logger.warning("Neo4j label lookup failed: {}", exc)
                self._labels_cache = set()
        return label in self._labels_cache

    def sync_document(self, session: Session, document: DocumentModel) -> None:
        """Upsert one document snapshot into Neo4j."""

        if not self.enabled:
            return

        mentions = session.execute(select(MentionModel).where(MentionModel.document_pk == document.pk)).scalars().all()
        entity_ids = {mention.entity_pk for mention in mentions}
        entities = {
            entity.pk: entity
            for entity in session.execute(select(EntityModel)).scalars().all()
            if entity.pk in entity_ids
        }
        relations = session.execute(select(RelationModel).where(RelationModel.document_pk == document.pk)).scalars().all()

        try:
            with self._driver.session() as neo4j_session:
                neo4j_session.run(
                    """
                    MERGE (d:Document {document_id: $document_id})
                    SET d.title = $title,
                        d.source = $source,
                        d.category = $category,
                        d.allowed_roles = $allowed_roles,
                        d.graph_version = $graph_version,
                        d.index_version = $index_version
                    """,
                    document_id=document.document_id,
                    title=document.title,
                    source=document.source,
                    category=document.category,
                    allowed_roles=document.allowed_roles or [],
                    graph_version=document.graph_version,
                    index_version=document.index_version,
                )
                for entity in entities.values():
                    display_name = next(iter(entity.aliases or [entity.canonical_name]), entity.canonical_name)
                    neo4j_session.run(
                        """
                        MERGE (e:Entity {entity_id: $entity_id})
                        SET e.name = $name,
                            e.category = $category,
                            e.aliases = $aliases
                        """,
                        entity_id=entity.entity_id,
                        name=display_name,
                        category=entity.category,
                        aliases=entity.aliases or [],
                    )
                    neo4j_session.run(
                        """
                        MATCH (d:Document {document_id: $document_id})
                        MATCH (e:Entity {entity_id: $entity_id})
                        MERGE (d)-[:MENTIONS]->(e)
                        """,
                        document_id=document.document_id,
                        entity_id=entity.entity_id,
                    )

                for relation in relations:
                    source_entity = entities.get(relation.source_entity_pk)
                    target_entity = entities.get(relation.target_entity_pk)
                    if source_entity is None or target_entity is None:
                        continue
                    relation_type = relation.relation_type.upper().replace("-", "_")
                    neo4j_session.run(
                        f"""
                        MATCH (s:Entity {{entity_id: $source_entity_id}})
                        MATCH (t:Entity {{entity_id: $target_entity_id}})
                        MERGE (s)-[r:{relation_type}]->(t)
                        SET r.confidence = $confidence,
                            r.document_id = $document_id
                        """,
                        source_entity_id=source_entity.entity_id,
                        target_entity_id=target_entity.entity_id,
                        confidence=relation.confidence,
                        document_id=document.document_id,
                    )
        except Exception as exc:
            logger.warning("Neo4j synchronization skipped for {}: {}", document.document_id, exc)

    def sync_communities(self, communities: Iterable[CommunityModel]) -> None:
        """Mirror rebuilt community summaries into Neo4j."""

        if not self.enabled:
            return

        try:
            with self._driver.session() as neo4j_session:
                for community in communities:
                    neo4j_session.run(
                        """
                        MERGE (c:Community {community_id: $community_id})
                        SET c.name = $name,
                            c.category = $category,
                            c.summary = $summary,
                            c.source_document_ids = $source_document_ids,
                            c.entity_names = $entity_names,
                            c.graph_version = $graph_version
                        """,
                        community_id=community.community_id,
                        name=community.name,
                        category=community.category,
                        summary=community.summary,
                        source_document_ids=community.source_document_ids or [],
                        entity_names=community.entity_names or [],
                        graph_version=community.graph_version,
                    )
                    neo4j_session.run(
                        """
                        MATCH (c:Community {community_id: $community_id})
                        OPTIONAL MATCH (c)-[r:HAS_DOCUMENT]->(:Document)
                        DELETE r
                        """,
                        community_id=community.community_id,
                    )
                    for document_id in community.source_document_ids or []:
                        neo4j_session.run(
                            """
                            MATCH (c:Community {community_id: $community_id})
                            MATCH (d:Document {document_id: $document_id})
                            MERGE (c)-[:HAS_DOCUMENT]->(d)
                            """,
                            community_id=community.community_id,
                            document_id=document_id,
                        )
            if self._labels_cache is not None:
                self._labels_cache.add("Community")
        except Exception as exc:
            logger.warning("Neo4j community synchronization skipped: {}", exc)

    def local_search(self, *, query_terms: set[str], visible_document_ids: set[str], limit: int) -> list[dict]:
        """Query entity neighborhoods from Neo4j for local graph search."""

        if not self.enabled or not query_terms or not visible_document_ids:
            return []

        cypher = """
        MATCH (d:Document)-[:MENTIONS]->(e:Entity)
        WHERE d.document_id IN $document_ids
          AND ANY(term IN $terms WHERE toLower(e.name) CONTAINS term OR ANY(alias IN coalesce(e.aliases, []) WHERE toLower(alias) CONTAINS term))
        OPTIONAL MATCH (e)-[r]->(neighbor:Entity)
        RETURN d.document_id AS document_id,
               d.title AS title,
               d.source AS source,
               e.name AS entity_name,
               e.category AS category,
               collect(DISTINCT neighbor.name)[0..5] AS neighbors,
               collect(DISTINCT type(r))[0..5] AS relations,
               size(collect(DISTINCT neighbor)) AS degree
        ORDER BY degree DESC, title ASC
        LIMIT $limit
        """
        try:
            with self._driver.session() as neo4j_session:
                result = neo4j_session.run(
                    cypher,
                    document_ids=list(visible_document_ids),
                    terms=sorted(query_terms),
                    limit=limit,
                )
                return [record.data() for record in result]
        except Exception as exc:
            logger.warning("Neo4j local search failed: {}", exc)
            return []

    def path_search(self, *, query_terms: set[str], visible_document_ids: set[str], limit: int) -> list[dict]:
        """Query short relationship paths between matched entities."""

        if not self.enabled or not query_terms or not visible_document_ids:
            return []

        cypher = """
        MATCH (d:Document)-[:MENTIONS]->(source:Entity)
        WHERE d.document_id IN $document_ids
          AND ANY(term IN $terms WHERE toLower(source.name) CONTAINS term OR ANY(alias IN coalesce(source.aliases, []) WHERE toLower(alias) CONTAINS term))
        MATCH path=(source)-[*1..2]-(target:Entity)
        WHERE source <> target
        RETURN DISTINCT d.title AS title,
               d.source AS source,
               source.name AS source_name,
               target.name AS target_name,
               [node IN nodes(path) | coalesce(node.name, node.title, node.document_id)] AS path_nodes,
               [rel IN relationships(path) | type(rel)] AS path_relations,
               length(path) AS hop_count
        ORDER BY hop_count ASC, title ASC
        LIMIT $limit
        """
        try:
            with self._driver.session() as neo4j_session:
                result = neo4j_session.run(
                    cypher,
                    document_ids=list(visible_document_ids),
                    terms=sorted(query_terms),
                    limit=limit,
                )
                return [record.data() for record in result]
        except Exception as exc:
            logger.warning("Neo4j path search failed: {}", exc)
            return []

    def global_search(self, *, query_terms: set[str], visible_document_ids: set[str], limit: int) -> list[dict]:
        """Query community summaries from Neo4j for global graph search."""

        if not self.enabled or not query_terms or not self.has_label("Community"):
            return []

        cypher = """
        MATCH (c:Community)
        WHERE ANY(term IN $terms WHERE toLower(c.name) CONTAINS term OR toLower(c.summary) CONTAINS term OR ANY(entity_name IN coalesce(c.entity_names, []) WHERE toLower(entity_name) CONTAINS term))
          AND ANY(document_id IN coalesce(c.source_document_ids, []) WHERE document_id IN $document_ids)
        RETURN c.community_id AS community_id,
               c.name AS name,
               c.category AS category,
               c.summary AS summary,
               c.source_document_ids AS source_document_ids,
               c.entity_names AS entity_names,
               size(coalesce(c.entity_names, [])) AS entity_count
        ORDER BY entity_count DESC, name ASC
        LIMIT $limit
        """
        try:
            with self._driver.session() as neo4j_session:
                result = neo4j_session.run(
                    cypher,
                    document_ids=list(visible_document_ids),
                    terms=sorted(query_terms),
                    limit=limit,
                )
                return [record.data() for record in result]
        except Exception as exc:
            logger.warning("Neo4j global search failed: {}", exc)
            return []

    def graph_snapshot(self, *, visible_document_ids: set[str]) -> dict[str, object] | None:
        """Read the current graph snapshot from Neo4j for the selected documents."""

        if not self.enabled or not visible_document_ids:
            return None

        try:
            with self._driver.session() as neo4j_session:
                node_rows = neo4j_session.run(
                    """
                    MATCH (d:Document)
                    WHERE d.document_id IN $document_ids
                    OPTIONAL MATCH (d)-[:MENTIONS]->(e:Entity)
                    RETURN d.document_id AS document_id,
                           d.title AS title,
                           d.source AS source,
                           d.category AS category,
                           collect(DISTINCT {
                               entity_id: e.entity_id,
                               name: e.name,
                               category: e.category
                           }) AS entities
                    """,
                    document_ids=list(visible_document_ids),
                )
                relation_rows = neo4j_session.run(
                    """
                    MATCH (d:Document)-[:MENTIONS]->(s:Entity)-[r]->(t:Entity)
                    WHERE d.document_id IN $document_ids
                    RETURN DISTINCT s.entity_id AS source_entity_id,
                           s.name AS source_name,
                           t.entity_id AS target_entity_id,
                           t.name AS target_name,
                           type(r) AS relation,
                           r.confidence AS confidence
                    """,
                    document_ids=list(visible_document_ids),
                )
                community_records: list[dict[str, object]] = []
                if self.has_label("Community"):
                    community_rows = neo4j_session.run(
                        """
                        MATCH (c:Community)
                        WHERE ANY(document_id IN coalesce(c.source_document_ids, []) WHERE document_id IN $document_ids)
                        RETURN c.community_id AS community_id,
                               c.name AS name,
                               c.category AS category,
                               c.summary AS summary,
                               c.source_document_ids AS source_document_ids,
                               c.entity_names AS entity_names
                        """,
                        document_ids=list(visible_document_ids),
                    )
                    community_records = [record.data() for record in community_rows]
                return {
                    "documents": [record.data() for record in node_rows],
                    "relations": [record.data() for record in relation_rows],
                    "communities": community_records,
                }
        except Exception as exc:
            logger.warning("Neo4j graph snapshot failed: {}", exc)
            return None
