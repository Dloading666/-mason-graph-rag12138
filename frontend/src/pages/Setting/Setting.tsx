import { Button, Card, Descriptions, Space, Table, Tag, Typography, message } from 'antd';
import { useEffect, useState } from 'react';

import platformApi from '@/api/platformApi';
import type { EvaluationRunResponse } from '@/types/qa';
import { getCurrentUser } from '@/utils/auth';
import { formatDateTime } from '@/utils/format';

const { Paragraph } = Typography;

const governanceItems = [
  {
    title: '认证与权限',
    copy: '当前以前端角色守卫 + 本地 JWT 为主，后续可以平滑切换到 LDAP、AD 或企业 SSO。',
  },
  {
    title: '模型与向量',
    copy: '问答默认走 DashScope 兼容模式，文本向量由可配置的 Embedding 模型提供。',
  },
  {
    title: '图谱扩展',
    copy: '现在已经支持 Neo4j 社区查询、路径推理和 SQL 回退，后续可以继续细化关系路径排序。', 
  },
];

export default function SettingPage() {
  const user = getCurrentUser();
  const [runs, setRuns] = useState<EvaluationRunResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);

  const loadRuns = async () => {
    setLoading(true);
    try {
      const response = await platformApi.listEvaluations();
      setRuns(response);
    } catch (error) {
      message.error('评估记录加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRuns();
  }, []);

  const handleRun = async () => {
    setRunning(true);
    try {
      const response = await platformApi.runEvaluation({
        name: `benchmark-${new Date().toISOString()}`,
        modes: ['naive', 'hybrid', 'fusion'],
      });
      message.success(`评估已完成：${response.run_id}`);
      await loadRuns();
    } catch (error) {
      message.error('评估运行失败');
    } finally {
      setRunning(false);
    }
  };

  return (
    <Space direction="vertical" size={20} style={{ width: '100%' }}>
      <Card className="page-card" bordered={false} title="系统配置与治理">
        <Descriptions column={1}>
          <Descriptions.Item label="当前角色">{user?.role ?? 'unknown'}</Descriptions.Item>
          <Descriptions.Item label="模型接入">DashScope / Qwen3.5-plus</Descriptions.Item>
          <Descriptions.Item label="向量模型">text-embedding-v4</Descriptions.Item>
          <Descriptions.Item label="图谱查询">Neo4j 优先，SQL 回退</Descriptions.Item>
          <Descriptions.Item label="部署模式">前后端分离 + Docker + 可选对象存储 / 队列</Descriptions.Item>
        </Descriptions>
        <Paragraph style={{ marginTop: 16 }}>
          当前治理页除了展示系统信息，也承担基线评估入口，方便管理员观察不同检索模式和图谱能力的表现差异。
        </Paragraph>
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          {governanceItems.map((item) => (
            <Card key={item.title} size="small" bordered={false}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>{item.title}</div>
              <div>{item.copy}</div>
            </Card>
          ))}
        </Space>
      </Card>

      <Card
        className="page-card"
        bordered={false}
        title="建材 Benchmark 评估"
        extra={
          <Button type="primary" onClick={() => void handleRun()} loading={running}>
            运行评估
          </Button>
        }
      >
        <Table
          rowKey="run_id"
          dataSource={runs}
          loading={loading}
          pagination={false}
          columns={[
            { title: 'Run ID', dataIndex: 'run_id', width: 180 },
            { title: '名称', dataIndex: 'name' },
            {
              title: '状态',
              dataIndex: 'status',
              width: 120,
              render: (value: string) => (
                <Tag color={value === 'completed' ? 'green' : value === 'failed' ? 'red' : 'blue'}>{value}</Tag>
              ),
            },
            {
              title: '领域覆盖',
              dataIndex: 'metrics',
              render: (value: Record<string, unknown>) => {
                const domains = (value?.domains as string[] | undefined) ?? [];
                return domains.length > 0 ? domains.join(' / ') : '--';
              },
            },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              width: 180,
              render: (value: string) => formatDateTime(value),
            },
            {
              title: '完成时间',
              dataIndex: 'finished_at',
              width: 180,
              render: (value?: string | null) => (value ? formatDateTime(value) : '--'),
            },
          ]}
          expandable={{
            expandedRowRender: (record) => (
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{JSON.stringify(record.metrics, null, 2)}</pre>
            ),
          }}
        />
      </Card>
    </Space>
  );
}
