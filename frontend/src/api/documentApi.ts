import api from '@/api';
import type { DocumentSummary, IngestResponse } from '@/types/document';

const documentApi = {
  async listDocuments(): Promise<DocumentSummary[]> {
    const { data } = await api.get<DocumentSummary[]>('/documents');
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

  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`);
  },
};

export default documentApi;

