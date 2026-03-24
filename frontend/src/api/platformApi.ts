import api from '@/api';
import type {
  EvaluationRunRequest,
  EvaluationRunResponse,
  FeedbackRequest,
  JobResponse,
  QaMode,
  ResearchJobResponse,
  TraceResponse,
} from '@/types/qa';

const platformApi = {
  async createResearchReport(question: string, mode: QaMode = 'fusion'): Promise<ResearchJobResponse> {
    const { data } = await api.post<ResearchJobResponse>('/research/report', { question, mode });
    return data;
  },

  async getJob(jobId: string): Promise<JobResponse> {
    const { data } = await api.get<JobResponse>(`/jobs/${jobId}`);
    return data;
  },

  async listJobs(limit = 50): Promise<JobResponse[]> {
    const { data } = await api.get<JobResponse[]>('/jobs', { params: { limit } });
    return data;
  },

  async listTraces(limit = 50): Promise<TraceResponse[]> {
    const { data } = await api.get<TraceResponse[]>('/traces', { params: { limit } });
    return data;
  },

  async submitFeedback(payload: FeedbackRequest): Promise<void> {
    await api.post('/feedback', payload);
  },

  async listEvaluations(): Promise<EvaluationRunResponse[]> {
    const { data } = await api.get<EvaluationRunResponse[]>('/evaluation/runs');
    return data;
  },

  async runEvaluation(payload: EvaluationRunRequest): Promise<EvaluationRunResponse> {
    const { data } = await api.post<EvaluationRunResponse>('/evaluation/run', payload);
    return data;
  },
};

export default platformApi;
