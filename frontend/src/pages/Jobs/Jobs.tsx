import { Button, Empty, Progress, Table, Tag, message } from 'antd';
import { useEffect, useMemo, useState } from 'react';

import platformApi from '@/api/platformApi';
import MetricStrip from '@/components/Surface/MetricStrip';
import SectionHeader from '@/components/Surface/SectionHeader';
import type { JobResponse } from '@/types/qa';
import { formatDateTime } from '@/utils/format';

function getJobTone(status: string) {
  if (status === 'completed') {
    return 'state-chip-success';
  }

  if (status === 'failed') {
    return 'state-chip-danger';
  }

  return 'state-chip-info';
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await platformApi.listJobs();
      setJobs(data);
    } catch {
      message.error('任务列表加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadJobs();
  }, []);

  const runningCount = jobs.filter((job) => !['completed', 'failed'].includes(job.status)).length;
  const completedCount = jobs.filter((job) => job.status === 'completed').length;
  const failedCount = jobs.filter((job) => job.status === 'failed').length;
  const typeSummary = useMemo(() => {
    const summary = jobs.reduce<Record<string, number>>((accumulator, job) => {
      accumulator[job.job_type] = (accumulator[job.job_type] ?? 0) + 1;
      return accumulator;
    }, {});

    return Object.entries(summary).sort((left, right) => right[1] - left[1]);
  }, [jobs]);

  const metrics = [
    {
      label: '任务总量',
      value: jobs.length,
      detail: '当前可追踪的异步任务数量。',
      tone: 'neutral' as const,
    },
    {
      label: '运行中',
      value: runningCount,
      detail: '仍在排队或执行中的任务。',
      tone: 'teal' as const,
    },
    {
      label: '已完成',
      value: completedCount,
      detail: '已返回结果的任务数量。',
      tone: 'amber' as const,
    },
    {
      label: '失败',
      value: failedCount,
      detail: '需要排查的任务数量。',
      tone: failedCount > 0 ? ('danger' as const) : ('neutral' as const),
    },
  ];

  return (
    <div className="workspace-page">
      <MetricStrip items={metrics} />

      <div className="workspace-grid workspace-grid-governance">
        <section className="surface">
          <SectionHeader
            eyebrow="Async Queue"
            title="任务清单"
            description="跟踪文档入库、研究报告与评估任务的状态、进度和结果摘要。"
            action={
              <Button onClick={() => void loadJobs()} loading={loading} className="button-secondary">
                刷新列表
              </Button>
            }
          />

          {jobs.length === 0 && !loading ? (
            <Empty className="empty-state" description="当前还没有任务记录。" />
          ) : (
            <div className="table-wrap">
              <Table
                rowKey="job_id"
                loading={loading}
                dataSource={jobs}
                pagination={false}
                className="data-table"
                columns={[
                  { title: '任务 ID', dataIndex: 'job_id', width: 220 },
                  { title: '类型', dataIndex: 'job_type', width: 160 },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    width: 120,
                    render: (value: string) => <Tag className={`state-chip ${getJobTone(value)}`}>{value}</Tag>,
                  },
                  {
                    title: '进度',
                    dataIndex: 'progress',
                    width: 180,
                    render: (value: number) => <Progress percent={Math.round((value ?? 0) * 100)} size="small" showInfo={false} />,
                  },
                  {
                    title: '结果摘要',
                    dataIndex: 'result',
                    render: (value: JobResponse['result']) => value?.answer ?? value?.mode ?? '--',
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
              />
            </div>
          )}
        </section>

        <aside className="workspace-aside">
          <section className="surface surface-sticky">
            <SectionHeader
              eyebrow="Queue Summary"
              title="队列摘要"
              description="快速识别当前积压、任务类型分布和最近活跃状态。"
            />

            <div className="inspector-list">
              <div className="inspector-card">
                <div className="inspector-label">当前积压</div>
                <div className="inspector-value">{runningCount}</div>
                <div className="inspector-copy">未完成任务越多，越需要关注队列吞吐和失败重试。</div>
              </div>
              <div className="inspector-card">
                <div className="inspector-label">最近完成</div>
                <div className="inspector-value">
                  {jobs.find((job) => job.status === 'completed')?.job_type ?? '暂无'}
                </div>
                <div className="inspector-copy">可结合追踪中心回看具体结果与引用。</div>
              </div>
            </div>

            <div className="resource-group">
              <div className="subsection-title">任务类型分布</div>
              {typeSummary.length === 0 ? (
                <div className="panel-note">暂无任务类型分布数据。</div>
              ) : (
                <div className="tag-list">
                  {typeSummary.map(([type, count]) => (
                    <Tag key={type} className="info-chip">
                      {type} · {count}
                    </Tag>
                  ))}
                </div>
              )}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
