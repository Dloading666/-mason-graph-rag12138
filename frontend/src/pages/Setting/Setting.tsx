import { Button, Empty, Table, Tag, message } from 'antd';
import { useEffect, useState } from 'react';

import platformApi from '@/api/platformApi';
import MetricStrip from '@/components/Surface/MetricStrip';
import SectionHeader from '@/components/Surface/SectionHeader';
import type { EvaluationRunResponse } from '@/types/qa';
import { getCurrentUser } from '@/utils/auth';
import { formatDateTime } from '@/utils/format';

const governanceItems = [
  {
    title: '认证与权限',
    copy: '当前以前端角色守卫和本地 JWT 为主，后续可平滑切换到 LDAP、AD 或企业 SSO。',
  },
  {
    title: '模型与向量',
    copy: '问答默认接入 DashScope 兼容模式，文本向量由可配置的 Embedding 模型提供。',
  },
  {
    title: '图谱扩展',
    copy: '当前已支持 Neo4j 社区查询、路径推理与 SQL 回退，可继续细化关系排序。',
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
    } catch {
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
    } catch {
      message.error('评估运行失败');
    } finally {
      setRunning(false);
    }
  };

  const completedCount = runs.filter((run) => run.status === 'completed').length;
  const failedCount = runs.filter((run) => run.status === 'failed').length;
  const latestRun = runs[0];
  const metrics = [
    {
      label: '当前角色',
      value: user?.role ?? 'unknown',
      detail: '治理页仅对管理员开放。',
      tone: 'neutral' as const,
    },
    {
      label: '评估总量',
      value: runs.length,
      detail: '历史 Benchmark 运行次数。',
      tone: 'teal' as const,
    },
    {
      label: '已完成',
      value: completedCount,
      detail: '已产出指标结果的评估次数。',
      tone: 'amber' as const,
    },
    {
      label: '失败',
      value: failedCount,
      detail: '需要回看日志和配置的评估次数。',
      tone: failedCount > 0 ? ('danger' as const) : ('neutral' as const),
    },
  ];

  return (
    <div className="workspace-page">
      <MetricStrip items={metrics} />

      <div className="workspace-grid workspace-grid-governance">
        <section className="surface">
          <SectionHeader
            eyebrow="Governance Snapshot"
            title="系统快照"
            description="查看当前部署能力、权限边界和治理要点，避免脱离平台真实能力做结论。"
          />

          <div className="definition-grid">
            <div className="definition-item">
              <div className="definition-label">模型接入</div>
              <div className="definition-value">DashScope / Qwen3.5-plus</div>
            </div>
            <div className="definition-item">
              <div className="definition-label">向量模型</div>
              <div className="definition-value">text-embedding-v4</div>
            </div>
            <div className="definition-item">
              <div className="definition-label">图谱查询</div>
              <div className="definition-value">Neo4j 优先，SQL 回退</div>
            </div>
            <div className="definition-item">
              <div className="definition-label">部署模式</div>
              <div className="definition-value">前后端分离 + Docker + 可选对象存储 / 队列</div>
            </div>
          </div>

          <div className="governance-list">
            {governanceItems.map((item) => (
              <div key={item.title} className="governance-item">
                <div className="subsection-title">{item.title}</div>
                <div className="panel-note">{item.copy}</div>
              </div>
            ))}
          </div>
        </section>

        <aside className="workspace-aside">
          <section className="surface surface-sticky">
            <SectionHeader
              eyebrow="Benchmark"
              title="评估控制台"
              description="用于比较不同检索模式的表现，并沉淀可回看的治理记录。"
            />

            <div className="inspector-list">
              <div className="inspector-card">
                <div className="inspector-label">最近评估</div>
                <div className="inspector-value">{latestRun?.name ?? '暂无记录'}</div>
                <div className="inspector-copy">
                  {latestRun ? `状态：${latestRun.status}` : '运行评估后会在下方列表沉淀历史结果。'}
                </div>
              </div>
              <div className="inspector-card">
                <div className="inspector-label">默认模式</div>
                <div className="inspector-value">naive / hybrid / fusion</div>
                <div className="inspector-copy">当前基线会并行比较三种模式，便于观察能力差异。</div>
              </div>
            </div>

            <Button type="primary" onClick={() => void handleRun()} loading={running} className="button-primary full-width">
              运行评估
            </Button>
          </section>
        </aside>
      </div>

      <section className="surface">
        <SectionHeader
          eyebrow="Evaluation History"
          title="评估记录"
          description="按运行批次查看状态、时间和领域覆盖，必要时展开指标详情。"
        />

        {runs.length === 0 && !loading ? (
          <Empty className="empty-state" description="当前还没有评估记录。" />
        ) : (
          <div className="table-wrap">
            <Table
              rowKey="run_id"
              dataSource={runs}
              loading={loading}
              pagination={false}
              className="data-table"
              columns={[
                { title: 'Run ID', dataIndex: 'run_id', width: 180 },
                { title: '名称', dataIndex: 'name' },
                {
                  title: '状态',
                  dataIndex: 'status',
                  width: 120,
                  render: (value: string) => (
                    <Tag className={`state-chip ${value === 'completed' ? 'state-chip-success' : value === 'failed' ? 'state-chip-danger' : 'state-chip-info'}`}>
                      {value}
                    </Tag>
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
                expandedRowRender: (record) => <pre className="json-block">{JSON.stringify(record.metrics, null, 2)}</pre>,
              }}
            />
          </div>
        )}
      </section>
    </div>
  );
}
