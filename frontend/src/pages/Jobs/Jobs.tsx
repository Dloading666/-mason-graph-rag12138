import { Button, Card, Progress, Space, Table, Tag, message } from 'antd';
import { useEffect, useState } from 'react';

import platformApi from '@/api/platformApi';
import type { JobResponse } from '@/types/qa';
import { formatDateTime } from '@/utils/format';

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await platformApi.listJobs();
      setJobs(data);
    } catch (error) {
      message.error('任务列表加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadJobs();
  }, []);

  return (
    <Space direction="vertical" size={20} style={{ width: '100%' }}>
      <Card
        className="page-card"
        bordered={false}
        title="任务中心"
        extra={
          <Button onClick={() => void loadJobs()} loading={loading}>
            刷新
          </Button>
        }
      >
        <Table
          rowKey="job_id"
          loading={loading}
          dataSource={jobs}
          pagination={false}
          columns={[
            { title: '任务 ID', dataIndex: 'job_id', width: 180 },
            { title: '类型', dataIndex: 'job_type', width: 160 },
            {
              title: '状态',
              dataIndex: 'status',
              width: 120,
              render: (value: string) => (
                <Tag color={value === 'completed' ? 'green' : value === 'failed' ? 'red' : 'blue'}>{value}</Tag>
              ),
            },
            {
              title: '进度',
              dataIndex: 'progress',
              width: 180,
              render: (value: number) => <Progress percent={Math.round((value ?? 0) * 100)} size="small" />,
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
      </Card>
    </Space>
  );
}
