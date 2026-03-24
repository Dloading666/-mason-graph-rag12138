import { DeleteOutlined, SyncOutlined, UploadOutlined } from '@ant-design/icons';
import { Button, Empty, Popconfirm, Select, Table, Tag, Upload, message } from 'antd';
import { useEffect, useState } from 'react';

import documentApi from '@/api/documentApi';
import type { DocumentSummary } from '@/types/document';
import { getCurrentUser } from '@/utils/auth';
import { formatDateTime } from '@/utils/format';

const roleOptions = [
  { label: '普通员工', value: 'normal' },
  { label: '采购岗', value: 'purchase' },
  { label: '管理员', value: 'admin' },
];

const categoryOptions = [
  { label: '通用', value: 'general' },
  { label: '施工规范', value: '施工规范' },
  { label: '采购制度', value: '采购制度' },
  { label: '产品手册', value: '产品手册' },
];

const roleLabelMap = Object.fromEntries(roleOptions.map((item) => [item.value, item.label]));

function renderStateChip(value: string) {
  if (value === 'indexed') {
    return <Tag className="state-chip state-chip-success">{value}</Tag>;
  }
  if (value === 'queued') {
    return <Tag className="state-chip state-chip-info">{value}</Tag>;
  }
  return <Tag className="state-chip state-chip-warning">{value}</Tag>;
}

export default function DocumentPage() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [category, setCategory] = useState('general');
  const [allowedRoles, setAllowedRoles] = useState<string[]>(['normal', 'purchase', 'admin']);
  const [uploading, setUploading] = useState(false);
  const user = getCurrentUser();

  const fetchDocuments = async () => {
    try {
      const response = await documentApi.listDocuments();
      setDocuments(response);
    } catch (error) {
      message.error('文档列表加载失败');
    }
  };

  useEffect(() => {
    void fetchDocuments();
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const response = await documentApi.uploadDocument(file, category, allowedRoles);
      message.success(`文档上传成功，当前状态：${response.ingestion_status}`);
      await fetchDocuments();
    } catch (error) {
      message.error('文档上传失败，请检查文件格式或稍后重试');
    } finally {
      setUploading(false);
    }
    return false;
  };

  const handleIngest = async (documentId: string) => {
    try {
      const response = await documentApi.ingestDocument(documentId);
      if (response.job_id) {
        message.success(`已提交入库任务：${response.job_id}`);
      } else {
        message.success(`文档已入库，生成 ${response.indexed_chunks} 个分块`);
      }
      await fetchDocuments();
    } catch (error) {
      message.error('增量入库失败');
    }
  };

  const handleDelete = async (documentId: string) => {
    try {
      await documentApi.deleteDocument(documentId);
      message.success('文档已删除');
      await fetchDocuments();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const canUpload = user?.role === 'admin' || user?.role === 'purchase';
  const canDelete = user?.role === 'admin';
  const indexedCount = documents.filter((item) => item.ingestion_status === 'indexed').length;
  const queuedCount = documents.filter((item) => item.ingestion_status === 'queued').length;
  const issueCount = documents.filter((item) => item.processing_errors.length > 0).length;
  const stats = [
    { label: '文档总量', value: documents.length, note: '当前知识源内可管理的文档数量。' },
    { label: '已完成入库', value: indexedCount, note: '已经生成向量或图谱索引，可用于问答检索。' },
    { label: '排队处理中', value: queuedCount, note: '正在等待异步任务完成的文档数量。' },
    { label: '处理异常', value: issueCount, note: '存在处理错误的文档会在展开行中展示原因。' },
  ];

  return (
    <div className="workspace-stack">
      <section className="page-hero">
        <div>
          <div className="page-kicker">Knowledge Ingestion</div>
          <h1 className="page-title">文档治理中心</h1>
          <p className="page-subtitle">
            管理上传、权限、增量入库与版本状态，让进入问答和图谱的知识源始终有清晰边界。
          </p>
          <div className="chip-cluster" style={{ marginTop: 18 }}>
            <Tag className="utility-chip">{canUpload ? '当前角色可上传' : '当前角色只读'}</Tag>
            <Tag className="utility-chip">{canDelete ? '允许删除文档' : '不允许删除文档'}</Tag>
          </div>
        </div>

        <div className="hero-stat-grid">
          <div className="hero-stat">
            <span>上传权限</span>
            <strong>{canUpload ? '启用' : '只读'}</strong>
            <div className="metric-note" style={{ color: 'rgba(228, 236, 242, 0.68)' }}>
              采购岗和管理员可上传并触发入库。
            </div>
          </div>
          <div className="hero-stat">
            <span>删除权限</span>
            <strong>{canDelete ? '启用' : '关闭'}</strong>
            <div className="metric-note" style={{ color: 'rgba(228, 236, 242, 0.68)' }}>
              删除操作仅对管理员开放。
            </div>
          </div>
        </div>
      </section>

      <section className="metric-grid">
        {stats.map((item) => (
          <div key={item.label} className="metric-tile">
            <div className="metric-label">{item.label}</div>
            <div className="metric-value">{item.value}</div>
            <div className="metric-note">{item.note}</div>
          </div>
        ))}
      </section>

      <section className="panel-surface">
        <div className="panel-heading">
          <div>
            <div className="section-eyebrow">Upload Control</div>
            <h2 className="panel-title">上传与权限设定</h2>
            <p className="panel-description">先设定分类与可见角色，再上传文档。上传成功后可以继续触发增量入库。</p>
          </div>
          <div className="panel-meta">当前角色：{roleLabelMap[user?.role ?? 'normal'] ?? user?.role ?? 'unknown'}</div>
        </div>

        <div className="toolbar-grid toolbar-grid-doc">
          <div className="field-stack">
            <span className="field-label">文档分类</span>
            <Select
              value={category}
              options={categoryOptions}
              onChange={setCategory}
              disabled={!canUpload}
            />
          </div>
          <div className="field-stack">
            <span className="field-label">可见角色</span>
            <Select
              mode="multiple"
              value={allowedRoles}
              options={roleOptions}
              onChange={setAllowedRoles}
              disabled={!canUpload}
            />
          </div>
          <div className="field-stack field-action">
            <span className="field-label">文档操作</span>
            <Upload beforeUpload={(file) => handleUpload(file)} showUploadList={false} disabled={!canUpload || uploading}>
              <Button
                icon={<UploadOutlined />}
                type="primary"
                loading={uploading}
                disabled={!canUpload}
                className="accent-button full-width"
              >
                上传文档
              </Button>
            </Upload>
          </div>
        </div>

        <div className="toolbar-note">文档上传后会保留业务状态、索引版本和图谱版本，便于后续排查知识来源。</div>
      </section>

      <section className="panel-surface">
        <div className="panel-heading">
          <div>
            <div className="section-eyebrow">Document Inventory</div>
            <h2 className="panel-title">文档清单</h2>
            <p className="panel-description">集中查看每份文档的来源、版本、角色范围和处理状态。</p>
          </div>
          <div className="panel-meta">总计 {documents.length} 份</div>
        </div>

        {documents.length === 0 ? (
          <Empty className="embedded-empty" description="当前还没有上传文档。" />
        ) : (
          <Table
            rowKey="document_id"
            dataSource={documents}
            pagination={false}
            scroll={{ x: 1320 }}
            className="industrial-table"
            columns={[
              { title: '标题', dataIndex: 'title', width: 220 },
              { title: '来源', dataIndex: 'source', width: 160 },
              { title: '分类', dataIndex: 'category', width: 120 },
              {
                title: '可见角色',
                dataIndex: 'allowed_roles',
                width: 200,
                render: (roles: string[]) => (
                  <div className="chip-cluster">
                    {roles.map((role) => (
                      <Tag key={role} className="utility-chip">
                        {roleLabelMap[role] ?? role}
                      </Tag>
                    ))}
                  </div>
                ),
              },
              {
                title: '业务状态',
                dataIndex: 'status',
                width: 120,
                render: (value: string) => renderStateChip(value),
              },
              {
                title: '入库状态',
                dataIndex: 'ingestion_status',
                width: 120,
                render: (value: string) => renderStateChip(value),
              },
              { title: '文档版本', dataIndex: 'version', width: 100 },
              { title: '图谱版本', dataIndex: 'graph_version', width: 100 },
              { title: '索引版本', dataIndex: 'index_version', width: 100 },
              {
                title: '最近更新',
                dataIndex: 'updated_at',
                width: 180,
                render: (value: string) => formatDateTime(value),
              },
              {
                title: '操作',
                key: 'actions',
                width: 180,
                render: (_, record: DocumentSummary) => (
                  <div className="chip-cluster">
                    <Button
                      icon={<SyncOutlined />}
                      onClick={() => handleIngest(record.document_id)}
                      disabled={!canUpload}
                      className="secondary-button"
                    >
                      入库
                    </Button>
                    <Popconfirm title="确认删除这份文档吗？" onConfirm={() => handleDelete(record.document_id)} disabled={!canDelete}>
                      <Button danger icon={<DeleteOutlined />} disabled={!canDelete}>
                        删除
                      </Button>
                    </Popconfirm>
                  </div>
                ),
              },
            ]}
            expandable={{
              expandedRowRender: (record) =>
                record.processing_errors.length > 0 ? (
                  <div className="chip-cluster">
                    {record.processing_errors.map((item) => (
                      <Tag key={item} className="state-chip state-chip-warning">
                        {item}
                      </Tag>
                    ))}
                  </div>
                ) : (
                  <span className="muted-copy">当前没有处理错误。</span>
                ),
            }}
          />
        )}
      </section>
    </div>
  );
}
