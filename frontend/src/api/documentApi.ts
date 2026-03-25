import api from '@/api';
import type {
  ChunkPreviewResponse,
  ChunkingConfig,
  DocumentSummary,
  IngestResponse,
  KnowledgeBaseSettings,
  RetrievalConfig,
  RetrievalTestResponse,
} from '@/types/document';

const documentApi = {
  async listDocuments(): Promise<DocumentSummary[]> {
    const { data } = await api.get<DocumentSummary[]>('/documents');
    return data;
  },

  async getKnowledgeBaseSettings(): Promise<KnowledgeBaseSettings> {
    const { data } = await api.get<KnowledgeBaseSettings>('/documents/settings');
    return data;
  },

  async updateKnowledgeBaseSettings(payload: KnowledgeBaseSettings): Promise<KnowledgeBaseSettings> {
    const { data } = await api.put<KnowledgeBaseSettings>('/documents/settings', payload);
    return data;
  },

  async uploadDocument(file: File, category: string, allowedRoles: string[]): Promise<DocumentSummary> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    formData.append('allowed_roles', allowedRoles.join(','));
    const { data } = await api.post<DocumentSummary>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  async ingestDocument(documentId: string): Promise<IngestResponse> {
    const { data } = await api.post<IngestResponse>(`/documents/${documentId}/ingest`);
    return data;
  },

  async previewChunks(documentId: string, chunking?: ChunkingConfig, limit = 8): Promise<ChunkPreviewResponse> {
    const { data } = await api.post<ChunkPreviewResponse>(`/documents/${documentId}/chunk-preview`, {
      chunking,
      limit,
    });
    return data;
  },

  async runRetrievalTest(question: string, retrieval?: RetrievalConfig): Promise<RetrievalTestResponse> {
    const { data } = await api.post<RetrievalTestResponse>('/documents/retrieval-test', {
      question,
      retrieval,
    });
    return data;
  },

  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`);
  },
};

export default documentApi;
