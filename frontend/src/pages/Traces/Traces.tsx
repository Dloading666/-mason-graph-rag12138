import { Collapse, Empty, Table, Tag, message } from 'antd';
import { useEffect, useMemo, useState } from 'react';

import platformApi from '@/api/platformApi';
import MetricStrip from '@/components/Surface/MetricStrip';
import SectionHeader from '@/components/Surface/SectionHeader';
import type { TraceResponse } from '@/types/qa';
import { formatDateTime } from '@/utils/format';

export default function TracesPage() {
  const [traces, setTraces] = useState<TraceResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTraces = async () => {
    setLoading(true);
    try {
      const data = await platformApi.listTraces();
      setTraces(data);
    } catch {
      message.error('追踪列表加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTraces();
  }, []);

  const modeSummary = useMemo(() => {
    const summary = traces.reduce<Record<string, number>>((accumulator, trace) => {
      accumulator[trace.mode] = (accumulator[trace.mode] ?? 0) + 1;
      return accumulator;
    }, {});

    return Object.entries(summary).sort((left, right) => right[1] - left[1]);
  }, [traces]);

  const totalCitations = traces.reduce((accumulator, trace) => accumulator + trace.citations.length, 0);
  const metrics = [
    {
      label: '追踪总量',
      value: traces.length,
      detail: '当前可回看的问答 Trace 记录数量。',
      tone: 'neutral' as const,
    },
    {
      label: '模式种类',
      value: modeSummary.length,
      detail: '出现过的问答模式数量。',
      tone: 'teal' as const,
    },
    {
      label: '引用总数',
      value: totalCitations,
      detail: '所有 Trace 累计返回的引用数量。',
      tone: 'amber' as const,
    },
    {
      label: '最近记录',
      value: traces[0] ? formatDateTime(traces[0].created_at) : '--',
      detail: '当前列表按时间倒序展示。',
      tone: 'neutral' as const,
    },
  ];

  return (
    <div className="workspace-page">
      <MetricStrip items={metrics} />

      <div className="workspace-grid workspace-grid-governance">
        <section className="surface">
          <SectionHeader
            eyebrow="Trace Audit"
            title="追踪记录"
            description="按问题、模式和时间回看答案、计划、调试信息与引用链路。"
          />

          {traces.length === 0 && !loading ? (
            <Empty className="empty-state" description="当前还没有可展示的追踪记录。" />
          ) : (
            <div className="table-wrap">
              <Table
                rowKey="trace_id"
                dataSource={traces}
                loading={loading}
                pagination={false}
                className="data-table"
                expandable={{
                  expandedRowRender: (record) => (
                    <div className="expand-shell">
                      <div className="audit-block">
                        <strong>回答</strong>
                        <p>{record.answer ?? '--'}</p>
                      </div>
                      <Collapse
                        items={[
                          {
                            key: `${record.trace_id}-detail`,
                            label: '计划 / 执行 / 调试',
                            children: (
                              <pre className="json-block">
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
                    </div>
                  ),
                }}
                columns={[
                  { title: 'Trace ID', dataIndex: 'trace_id', width: 220 },
                  { title: '问题', dataIndex: 'question' },
                  {
                    title: '模式',
                    dataIndex: 'mode',
                    width: 130,
                    render: (value: string) => <Tag className="info-chip">{value}</Tag>,
                  },
                  {
                    title: '引用',
                    dataIndex: 'citations',
                    width: 240,
                    render: (value: string[]) =>
                      value.length === 0 ? (
                        '--'
                      ) : (
                        <div className="tag-list">
                          {value.map((item) => (
                            <Tag key={item} className="info-chip">
                              {item}
                            </Tag>
                          ))}
                        </div>
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
            </div>
          )}
        </section>

        <aside className="workspace-aside">
          <section className="surface surface-sticky">
            <SectionHeader
              eyebrow="Audit Summary"
              title="审计摘要"
              description="帮助判断当前平台最常用的模式和最近一次问答轨迹。"
            />

            <div className="inspector-list">
              <div className="inspector-card">
                <div className="inspector-label">最近问题</div>
                <div className="inspector-value">{traces[0]?.question ?? '暂无'}</div>
                <div className="inspector-copy">列表默认按时间倒序，可直接展开查看详细链路。</div>
              </div>
              <div className="inspector-card">
                <div className="inspector-label">最常用模式</div>
                <div className="inspector-value">{modeSummary[0]?.[0] ?? '暂无'}</div>
                <div className="inspector-copy">如果模式长期单一，可回到评估中心比较不同检索效果。</div>
              </div>
            </div>

            <div className="resource-group">
              <div className="subsection-title">模式分布</div>
              <div className="tag-list">
                {modeSummary.slice(0, 6).map(([mode, count]) => (
                  <Tag key={mode} className="info-chip">
                    {mode} · {count}
                  </Tag>
                ))}
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
