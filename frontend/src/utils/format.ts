import type { EvidenceItem } from '@/types/qa';

export function formatEvidenceScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function buildCitationLabel(evidence: EvidenceItem): string {
  return `${evidence.source} · ${evidence.citation}`;
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN');
}

