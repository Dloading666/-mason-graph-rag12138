import { Card, Collapse, Empty, Space, Table, Tag, Typography, message } from 'antd';
import { useEffect, useState } from 'react';

import platformApi from '@/api/platformApi';
import type { TraceResponse } from '@/types/qa';
import { formatDateTime } from '@/utils/format';

const { Paragraph, Text } = Typography;

export default function TracesPage() {
  const [traces, setTraces] = useState<TraceResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTraces = async () => {
    setLoading(true);
    try {
      const data = await platformApi.listTraces();
      setTraces(data);
    } catch (error) {
      message.error('追踪列表加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTraces();
  }, []);

  return (
    <Card className="page-card" bordered={false} title="追踪中心">
      {traces.length === 0 ? (
        <Empty description="当前还没有可展示的追踪记录。" />
      ) : (
        <Table
          rowKey="trace_id"
          dataSource={traces}
          loading={loading}
          pagination={false}
          expandable={{
            expandedRowRender: (record) => (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <div>
                  <Text strong>回答</Text>
                  <Paragraph>{record.answer ?? '--'}</Paragraph>
                </div>
                <Collapse
                  items={[
                    {
                      key: `${record.trace_id}-detail`,
                      label: '计划 / 执行 / 调试',
                      children: (
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                          {JSON.stringify(
                            {
                              plan: record.plan,
                              execution_summary: record.execution_summary,
                              debug: record.debug,
                            },
                            null,
                            2,
                          )}
                        </pre>
                      ),
                    },
                  ]}
                />
              </Space>
            ),
          }}
          columns={[
            { title: 'Trace ID', dataIndex: 'trace_id', width: 180 },
            { title: '问题', dataIndex: 'question' },
            {
              title: '模式',
              dataIndex: 'mode',
              width: 120,
              render: (value: string) => <Tag color="blue">{value}</Tag>,
            },
            {
              title: '引用',
              dataIndex: 'citations',
              width: 220,
              render: (value: string[]) => (
                <Space wrap>
                  {value.length === 0 ? '--' : value.map((item) => <Tag key={item}>{item}</Tag>)}
                </Space>
              ),
            },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              width: 180,
              render: (value: string) => formatDateTime(value),
            },
          ]}
        />
      )}
    </Card>
  );
}
