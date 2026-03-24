export interface GraphNode {
  id: string;
  name: string;
  category: string;
  source_documents: string[];
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight?: number;
}

export interface GraphCommunity {
  community_id: string;
  name: string;
  category: string;
  summary: string;
  source_documents: string[];
  entity_names: string[];
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  communities: GraphCommunity[];
  source_documents: string[];
  entity_neighbors: Record<string, string[]>;
}
