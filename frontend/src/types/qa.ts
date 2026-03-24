export type QaMode = 'auto' | 'naive' | 'local' | 'global' | 'hybrid' | 'deep_research' | 'fusion';

export interface EvidenceItem {
  title: string;
  source: string;
  snippet: string;
  citation: string;
  score: number;
}

export interface QaRequest {
  question: string;
  need_evidence: boolean;
  mode?: QaMode;
  debug?: boolean;
}

export interface QaResponse {
  answer: string;
  evidence: EvidenceItem[];
  citations: string[];
  trace_id: string;
  mode: string;
  plan?: Record<string, unknown> | null;
  execution_summary?: Record<string, unknown> | null;
  debug?: Record<string, unknown> | null;
}

export interface QaStreamStageEvent {
  type: 'stage';
  data: {
    stage: string;
  };
}

export interface QaStreamAnswerEvent {
  type: 'answer';
  data: QaResponse;
}

export interface QaStreamDoneEvent {
  type: 'done';
  data: {
    status: string;
  };
}

export type QaStreamEvent = QaStreamStageEvent | QaStreamAnswerEvent | QaStreamDoneEvent;

export interface ResearchJobResponse {
  job_id: string;
  status: string;
}

export interface JobResponse {
  job_id: string;
  job_type: string;
  status: string;
  progress: number;
  document_id?: string | null;
  trace_id?: string | null;
  result?: {
    answer?: string;
    mode?: string;
    trace_id?: string;
    citations?: string[];
    plan?: Record<string, unknown> | null;
    execution_summary?: Record<string, unknown> | null;
  } | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  finished_at?: string | null;
}

export interface FeedbackRequest {
  trace_id: string;
  rating?: number;
  sentiment?: string;
  comment?: string;
}

export interface TraceResponse {
  trace_id: string;
  question: string;
  user_role: string;
  mode: string;
  answer?: string | null;
  plan?: Record<string, unknown> | null;
  execution_summary?: Record<string, unknown> | null;
  debug?: Record<string, unknown> | null;
  citations: string[];
  created_at: string;
}

export interface EvaluationRunRequest {
  name: string;
  modes: QaMode[];
}

export interface EvaluationRunResponse {
  run_id: string;
  name: string;
  status: string;
  metrics: Record<string, unknown>;
  notes?: string | null;
  created_at: string;
  finished_at?: string | null;
}

export interface ConversationMessage {
  id: string;
  traceId: string;
  question: string;
  answer: string;
  evidence: EvidenceItem[];
  citations: string[];
  mode: string;
  plan?: Record<string, unknown> | null;
  executionSummary?: Record<string, unknown> | null;
  debug?: Record<string, unknown> | null;
  createdAt: string;
}
