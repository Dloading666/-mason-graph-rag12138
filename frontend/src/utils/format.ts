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

export function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return '0 B';
  }

  const units = ['B', 'KB', 'MB', 'GB'];
  const exponent = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  const converted = value / 1024 ** exponent;

  return `${converted.toFixed(converted >= 100 || exponent === 0 ? 0 : 2)} ${units[exponent]}`;
}
