import { Empty, List, Space, Tag, Typography } from 'antd';

import type { EvidenceItem } from '@/types/qa';
import { buildCitationLabel, formatEvidenceScore } from '@/utils/format';

const { Text, Paragraph } = Typography;

interface EvidencePanelProps {
  evidence: EvidenceItem[];
}

export default function EvidencePanel({ evidence }: EvidencePanelProps) {
  return (
    <div className="evidence-panel">
      <div className="evidence-panel-header">
        <div>
          <div className="section-eyebrow">Evidence Trace</div>
          <div className="panel-title panel-title-sm">证据链</div>
        </div>
        <Tag className="utility-chip">{evidence.length} 条</Tag>
      </div>

      {evidence.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="当前回答没有返回证据片段。"
          className="embedded-empty"
        />
      ) : (
        <List
          split={false}
          dataSource={evidence}
          className="evidence-list"
          renderItem={(item) => (
            <List.Item className="evidence-item">
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                <Space wrap className="evidence-title-row">
                  <Text strong className="evidence-title">
                    {item.title}
                  </Text>
                  <Tag className="score-chip">{formatEvidenceScore(item.score)}</Tag>
                  <Tag className="citation-chip">{buildCitationLabel(item)}</Tag>
                </Space>
                <Paragraph className="evidence-snippet">{item.snippet}</Paragraph>
              </Space>
            </List.Item>
          )}
        />
      )}
    </div>
  );
}
