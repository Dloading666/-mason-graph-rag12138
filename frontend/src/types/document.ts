import type { UserRole } from '@/types/user';
import type { QaMode } from '@/types/qa';

export interface DocumentSummary {
  document_id: string;
  title: string;
  source: string;
  category: string;
  allowed_roles: UserRole[];
  status: string;
  ingestion_status: string;
  version: number;
  graph_version: number;
  index_version: number;
  processing_errors: string[];
  file_size: number;
  char_count: number;
  chunk_count: number;
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface IngestResponse {
  document_id: string;
  status: string;
  indexed_chunks: number;
  job_id?: string | null;
}

export interface ChunkingConfig {
  mode: 'general';
  separator: string;
  max_length: number;
  overlap: number;
  normalize_whitespace: boolean;
  strip_urls_emails: boolean;
}

export interface RetrievalConfig {
  mode: QaMode;
  semantic_weight: number;
  keyword_weight: number;
  top_k: number;
  score_threshold_enabled: boolean;
  score_threshold: number;
}

export interface KnowledgeBaseSettings {
  chunking: ChunkingConfig;
  retrieval: RetrievalConfig;
}

export interface ChunkPreviewItem {
  index: number;
  content: string;
  character_count: number;
}

export interface ChunkPreviewResponse {
  document_id: string;
  title: string;
  total_chunks: number;
  total_characters: number;
  chunks: ChunkPreviewItem[];
}

export interface RetrievalTestRequest {
  question: string;
  retrieval?: RetrievalConfig;
}

export interface RetrievalTestHit {
  rank: number;
  title: string;
  source: string;
  citation: string;
  chunk_label: string;
  snippet: string;
  character_count: number;
  score: number;
}

export interface RetrievalTestResponse {
  question: string;
  mode: string;
  duration_ms: number;
  total_hits: number;
  hits: RetrievalTestHit[];
  debug?: Record<string, unknown> | null;
}
