"""Build a graph snapshot from accessible documents."""

from __future__ import annotations

from backend.core.contracts import DocumentRecord, GraphEdge, GraphNode, GraphResponse
from backend.graph.entity_extractor import EntityExtractor


class GraphBuilder:
    """Build a read-only graph representation from current documents."""

    def __init__(self) -> None:
        self.extractor = EntityExtractor()

    def build(self, documents: list[DocumentRecord]) -> GraphResponse:
        node_map: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        source_documents: list[str] = []

        for document in documents:
            source_documents.append(document.source)
            document_node_id = f"doc:{document.document_id}"
            node_map[document_node_id] = GraphNode(
                id=document_node_id,
                name=document.title,
                category="文档",
                source_documents=[document.source],
            )
            for entity in self.extractor.extract(document):
                entity_node_id = f"entity:{entity['category']}:{entity['name']}"
                if entity_node_id not in node_map:
                    node_map[entity_node_id] = GraphNode(
                        id=entity_node_id,
                        name=entity["name"],
                        category=entity["category"],
                        source_documents=[document.source],
                    )
                else:
                    node_map[entity_node_id].source_documents = sorted(
                        set(node_map[entity_node_id].source_documents + [document.source])
                    )
                edges.append(
                    GraphEdge(
                        source=document_node_id,
                        target=entity_node_id,
                        relation="文档-提及",
                    )
                )

        return GraphResponse(
            nodes=list(node_map.values()),
            edges=edges,
            source_documents=sorted(set(source_documents)),
        )

