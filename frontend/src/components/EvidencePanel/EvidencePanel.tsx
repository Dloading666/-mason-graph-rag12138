import { Empty, Tag } from 'antd';

import type { EvidenceItem } from '@/types/qa';
import { buildCitationLabel, formatEvidenceScore } from '@/utils/format';

interface EvidencePanelProps {
  evidence: EvidenceItem[];
}

export default function EvidencePanel({ evidence }: EvidencePanelProps) {
  return (
    <div className="evidence-shell">
      <div className="evidence-head">
        <div>
          <div className="surface-eyebrow">Evidence Trace</div>
          <div className="subsection-title">证据链</div>
        </div>
        <Tag className="info-chip">{evidence.length} 条</Tag>
      </div>

      {evidence.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前回答没有返回证据片段。" className="empty-state" />
      ) : (
        <div className="evidence-list">
          {evidence.map((item) => (
            <div key={`${item.title}-${item.citation}`} className="evidence-item">
              <div className="evidence-title-row">
                <div className="evidence-title">{item.title}</div>
                <div className="evidence-meta">
                  <Tag className="score-chip">{formatEvidenceScore(item.score)}</Tag>
                  <Tag className="info-chip">{buildCitationLabel(item)}</Tag>
                </div>
              </div>
              <div className="evidence-snippet">{item.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
