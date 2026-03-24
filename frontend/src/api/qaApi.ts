import api, { API_BASE_URL } from '@/api';
import { clearSession, getToken } from '@/utils/auth';
import type { QaRequest, QaResponse, QaStreamEvent } from '@/types/qa';

interface StreamOptions {
  onEvent?: (event: QaStreamEvent) => void;
}

const STREAM_URL = `${API_BASE_URL.replace(/\/$/, '')}/qa/ask-stream`;

function parseSseEvent(rawEvent: string): QaStreamEvent | null {
  const normalized = rawEvent.replace(/\r\n/g, '\n').trim();
  if (!normalized) {
    return null;
  }

  const lines = normalized.split('\n');
  let eventType = '';
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith('event:')) {
      eventType = line.slice(6).trim();
      continue;
    }

    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (!eventType) {
    return null;
  }

  const payload = dataLines.join('\n');
  if (!payload) {
    return null;
  }

  if (eventType === 'stage') {
    const data = JSON.parse(payload) as QaStreamEvent['data'];
    return { type: 'stage', data: { stage: String((data as { stage?: string }).stage ?? '') } };
  }

  if (eventType === 'answer') {
    return { type: 'answer', data: JSON.parse(payload) as QaResponse };
  }

  if (eventType === 'done') {
    const data = JSON.parse(payload) as { status?: string };
    return { type: 'done', data: { status: String(data.status ?? 'completed') } };
  }

  return null;
}

const qaApi = {
  async askQuestion(payload: QaRequest): Promise<QaResponse> {
    const { data } = await api.post<QaResponse>('/qa/ask', payload);
    return data;
  },

  async askQuestionStream(payload: QaRequest, options: StreamOptions = {}): Promise<void> {
    const token = getToken();
    const response = await fetch(STREAM_URL, {
      method: 'POST',
      headers: {
        Accept: 'text/event-stream',
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (response.status === 401) {
      clearSession();
      throw new Error('unauthorized');
    }

    if (!response.ok || !response.body) {
      throw new Error(`stream request failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    const flushEvents = (chunk: string) => {
      buffer += chunk;

      while (buffer.includes('\n\n')) {
        const splitIndex = buffer.indexOf('\n\n');
        const rawEvent = buffer.slice(0, splitIndex);
        buffer = buffer.slice(splitIndex + 2);

        const parsedEvent = parseSseEvent(rawEvent);
        if (parsedEvent) {
          options.onEvent?.(parsedEvent);
        }
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        flushEvents(decoder.decode());
        break;
      }

      flushEvents(decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n'));
    }

    const trailingEvent = parseSseEvent(buffer);
    if (trailingEvent) {
      options.onEvent?.(trailingEvent);
    }
  },
};

export default qaApi;
