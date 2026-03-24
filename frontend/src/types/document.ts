import type { UserRole } from '@/types/user';

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
  updated_at: string;
}

export interface IngestResponse {
  document_id: string;
  status: string;
  indexed_chunks: number;
  job_id?: string | null;
}
