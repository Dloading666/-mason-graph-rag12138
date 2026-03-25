import {
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  SearchOutlined,
  SettingOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import {
  Button,
  Drawer,
  Empty,
  Input,
  InputNumber,
  Popconfirm,
  Progress,
  Segmented,
  Select,
  Slider,
  Spin,
  Switch,
  Table,
  Tag,
  Upload,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useEffect, useMemo, useState } from 'react';

import documentApi from '@/api/documentApi';
import MetricStrip from '@/components/Surface/MetricStrip';
import SectionHeader from '@/components/Surface/SectionHeader';
import type {
  ChunkingConfig,
  ChunkPreviewResponse,
  DocumentSummary,
  KnowledgeBaseSettings,
  RetrievalConfig,
  RetrievalTestResponse,
} from '@/types/document';
import type { QaMode } from '@/types/qa';
import { getCurrentUser } from '@/utils/auth';
import { formatBytes, formatDateTime } from '@/utils/format';

type ViewMode = 'documents' | 'retrieval';

const DEFAULT_SETTINGS: KnowledgeBaseSettings = {
  chunking: {
    mode: 'general',
    separator: '\\n\\n',
    max_length: 1024,
    overlap: 50,
    normalize_whitespace: false,
    strip_urls_emails: false,
  },
  retrieval: {
    mode: 'hybrid',
    semantic_weight: 0.7,
    keyword_weight: 0.3,
    top_k: 5,
    score_threshold_enabled: false,
    score_threshold: 0.5,
  },
};

const roleOptions = [
  { label: '普通员工', value: 'normal' },
  { label: '采购岗', value: 'purchase' },
  { label: '管理员', value: 'admin' },
];

const categoryOptions = [
  { label: '通用资料', value: 'general' },
  { label: '施工规范', value: '施工规范' },
  { label: '采购制度', value: '采购制度' },
  { label: '产品手册', value: '产品手册' },
];

const retrievalModeOptions: Array<{ label: string; value: QaMode }> = [
  { label: '自动', value: 'auto' },
  { label: '全文 / 语义', value: 'naive' },
  { label: '局部图谱', value: 'local' },
  { label: '社区摘要', value: 'global' },
  { label: '混合检索', value: 'hybrid' },
  { label: 'Fusion', value: 'fusion' },
];

const roleLabelMap = Object.fromEntries(roleOptions.map((item) => [item.value, item.label]));
const retrievalModeLabelMap = Object.fromEntries(retrievalModeOptions.map((item) => [item.value, item.label]));

function getStatusChip(value: string) {
  const normalized = value.toLowerCase();
  const labelMap: Record<string, string> = {
    indexed: '已入库',
    queued: '排队中',
    uploaded: '已上传',
    ready: '就绪',
    failed: '失败',
    error: '异常',
    processing: '处理中',
    pending: '待导入',
    up_to_date: '最新',
  };
  const tone = normalized === 'indexed' || normalized === 'up_to_date'
    ? 'state-chip-success'
    : normalized === 'queued' || normalized === 'processing' || normalized === 'pending'
      ? 'state-chip-info'
      : normalized === 'failed' || normalized === 'error'
        ? 'state-chip-danger'
        : 'state-chip-neutral';

  return <Tag className={`state-chip ${tone}`}>{labelMap[normalized] ?? value}</Tag>;
}

export default function DocumentPage() {
  const user = getCurrentUser();
  const [viewMode, setViewMode] = useState<ViewMode>('documents');
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [settings, setSettings] = useState<KnowledgeBaseSettings>(DEFAULT_SETTINGS);
  const [draftSettings, setDraftSettings] = useState<KnowledgeBaseSettings>(DEFAULT_SETTINGS);
  const [searchText, setSearchText] = useState('');
  const [category, setCategory] = useState('general');
  const [allowedRoles, setAllowedRoles] = useState<string[]>(['normal', 'purchase', 'admin']);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [loadingSettings, setLoadingSettings] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [previewDocumentId, setPreviewDocumentId] = useState<string>();
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewResult, setPreviewResult] = useState<ChunkPreviewResponse | null>(null);
  const [retrievalQuestion, setRetrievalQuestion] = useState('');
  const [retrievalTesting, setRetrievalTesting] = useState(false);
  const [retrievalResult, setRetrievalResult] = useState<RetrievalTestResponse | null>(null);

  const canUpload = user?.role === 'admin' || user?.role === 'purchase';
  const canDelete = user?.role === 'admin';

  const loadDocuments = async (silent = false) => {
    if (!silent) {
      setLoadingDocuments(true);
    }
    try {
      const response = await documentApi.listDocuments();
      setDocuments(response);
      if (!previewDocumentId && response[0]) {
        setPreviewDocumentId(response[0].document_id);
      }
    } catch {
      message.error('文档列表加载失败');
    } finally {
      if (!silent) {
        setLoadingDocuments(false);
      }
    }
  };

  const loadSettings = async (silent = false) => {
    if (!silent) {
      setLoadingSettings(true);
    }
    try {
      const response = await documentApi.getKnowledgeBaseSettings();
      setSettings(response);
      setDraftSettings(response);
    } catch {
      message.error('知识库设置加载失败');
    } finally {
      if (!silent) {
        setLoadingSettings(false);
      }
    }
  };

  useEffect(() => {
    void Promise.all([loadDocuments(), loadSettings()]);
  }, []);

  useEffect(() => {
    if (!documents.some((item) => ['queued', 'processing'].includes(item.ingestion_status))) {
      return;
    }
    const timer = window.setInterval(() => {
      void loadDocuments(true);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [documents]);

  const totalStorage = useMemo(() => documents.reduce((sum, item) => sum + item.file_size, 0), [documents]);
  const totalChunks = useMemo(() => documents.reduce((sum, item) => sum + item.chunk_count, 0), [documents]);
  const indexedCount = useMemo(
    () => documents.filter((item) => item.ingestion_status === 'indexed' || item.ingestion_status === 'up_to_date').length,
    [documents],
  );
  const processingCount = useMemo(
    () => documents.filter((item) => ['queued', 'processing'].includes(item.ingestion_status)).length,
    [documents],
  );

  const filteredDocuments = useMemo(() => {
    const keyword = searchText.trim().toLowerCase();
    if (!keyword) {
      return documents;
    }
    return documents.filter((item) =>
      [item.title, item.source, item.category].some((field) => field.toLowerCase().includes(keyword)),
    );
  }, [documents, searchText]);

  const metrics = [
    { label: '文档总量', value: documents.length, detail: '当前知识库中已登记的文档数量。', tone: 'neutral' as const },
    { label: '已入库文档', value: indexedCount, detail: '已完成切块和知识库导入的文档数量。', tone: 'teal' as const },
    { label: '分块总数', value: totalChunks.toLocaleString('zh-CN'), detail: '当前累计可召回片段数量。', tone: 'amber' as const },
    { label: '存储占用', value: formatBytes(totalStorage), detail: '原始文档文件占用空间。', tone: 'neutral' as const },
  ];

  const updateDraftChunking = <K extends keyof ChunkingConfig>(key: K, value: ChunkingConfig[K]) => {
    setDraftSettings((current) => ({ ...current, chunking: { ...current.chunking, [key]: value } }));
  };

  const updateDraftRetrieval = <K extends keyof RetrievalConfig>(key: K, value: RetrievalConfig[K]) => {
    setDraftSettings((current) => ({ ...current, retrieval: { ...current.retrieval, [key]: value } }));
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const response = await documentApi.uploadDocument(file, category, allowedRoles);
      message.success(`文档已加入知识库队列，当前状态：${response.ingestion_status}`);
      await loadDocuments(true);
    } catch {
      message.error('文档上传失败，请检查文件格式后重试');
    } finally {
      setUploading(false);
    }
    return false;
  };

  const handleIngest = async (documentId: string) => {
    try {
      const response = await documentApi.ingestDocument(documentId);
      message.success(response.job_id ? `已提交导入任务：${response.job_id}` : `导入完成，共 ${response.indexed_chunks} 个分块`);
      await loadDocuments(true);
    } catch {
      message.error('文档切块导入失败');
    }
  };

  const handleDelete = async (documentId: string) => {
    try {
      await documentApi.deleteDocument(documentId);
      message.success('文档已删除');
      await loadDocuments(true);
    } catch {
      message.error('删除失败，请稍后重试');
    }
  };

  const handleSaveSettings = async () => {
    try {
      const response = await documentApi.updateKnowledgeBaseSettings(draftSettings);
      setSettings(response);
      setDraftSettings(response);
      message.success('知识库设置已保存');
    } catch {
      message.error('保存设置失败，请检查参数配置');
    }
  };

  const handlePreviewChunks = async () => {
    if (!previewDocumentId) {
      message.warning('请先选择预览文档');
      return;
    }
    setPreviewLoading(true);
    try {
      const response = await documentApi.previewChunks(previewDocumentId, draftSettings.chunking, 8);
      setPreviewResult(response);
    } catch {
      message.error('切块预览失败');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleRetrievalTest = async () => {
    const question = retrievalQuestion.trim();
    if (!question) {
      message.warning('请输入召回测试问题');
      return;
    }
    setRetrievalTesting(true);
    try {
      const response = await documentApi.runRetrievalTest(question, settings.retrieval);
      setRetrievalResult(response);
    } catch {
      message.error('召回测试失败');
    } finally {
      setRetrievalTesting(false);
    }
  };

  const columns: ColumnsType<DocumentSummary> = [
    {
      title: '文件名',
      dataIndex: 'title',
      width: 280,
      render: (_, record) => (
        <div className="document-title-cell">
          <div className="document-title-main">{record.title}</div>
          <div className="document-title-meta">{record.category}</div>
        </div>
      ),
    },
    { title: '文件大小', dataIndex: 'file_size', width: 120, render: (value: number) => formatBytes(value) },
    { title: '状态', dataIndex: 'status', width: 110, render: (value: string) => getStatusChip(value) },
    {
      title: '字符数',
      dataIndex: 'char_count',
      width: 120,
      render: (value: number) => <span className="document-accent-value">{value.toLocaleString('zh-CN')}</span>,
    },
    { title: '分块数', dataIndex: 'chunk_count', width: 110, render: (value: number) => <Tag className="info-chip">{value}</Tag> },
    { title: '导入状态', dataIndex: 'ingestion_status', width: 120, render: (value: string) => getStatusChip(value) },
    {
      title: '处理进度',
      dataIndex: 'progress',
      width: 180,
      render: (value: number) => <Progress percent={Math.round((value ?? 0) * 100)} size="small" />,
    },
    { title: '上传时间', dataIndex: 'created_at', width: 180, render: (value: string) => formatDateTime(value) },
    {
      title: '操作',
      key: 'actions',
      width: 240,
      render: (_, record) => (
        <div className="table-actions">
          <Button size="small" className="button-secondary" icon={<EyeOutlined />} onClick={() => {
            setSettingsOpen(true);
            setDraftSettings(settings);
            setPreviewResult(null);
            setPreviewDocumentId(record.document_id);
          }}>
            预览切块
          </Button>
          <Button size="small" className="button-secondary" icon={<ReloadOutlined />} onClick={() => void handleIngest(record.document_id)}>
            切块导入
          </Button>
          <Popconfirm
            title="确认删除文档？"
            description="删除后会移除该文档及其分块索引。"
            onConfirm={() => void handleDelete(record.document_id)}
            disabled={!canDelete}
          >
            <Button size="small" danger disabled={!canDelete} className="button-secondary" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </div>
      ),
    },
  ];

  return (
    <div className="workspace-page">
      <MetricStrip items={metrics} />

      <div className="workspace-grid workspace-grid-governance knowledge-governance-grid">
        <div className="workspace-main-column">
          <section className="surface surface-strong">
            <SectionHeader
              eyebrow="Knowledge Base Governance"
              title="文档治理工作台"
              description="统一管理文档上传、切块配置、知识库导入和召回测试。"
              meta={`${retrievalModeLabelMap[settings.retrieval.mode] ?? settings.retrieval.mode} · Top ${settings.retrieval.top_k}`}
              action={(
                <div className="surface-actions">
                  <Button className="button-secondary" icon={<ReloadOutlined />} onClick={() => void loadDocuments()}>
                    刷新
                  </Button>
                  <Button className="button-secondary" icon={<SettingOutlined />} onClick={() => {
                    setSettingsOpen(true);
                    setDraftSettings(settings);
                    setPreviewResult(null);
                  }}>
                    切块 / 检索设置
                  </Button>
                </div>
              )}
            />

            <div className="status-inline-grid">
              <div className="inline-status-card">
                <div className="inline-status-label">分段策略</div>
                <div className="inline-status-value">通用分段</div>
                <div className="inline-status-copy">
                  标识符 {settings.chunking.separator}，单块长度 {settings.chunking.max_length}，重叠 {settings.chunking.overlap}。
                </div>
              </div>
              <div className="inline-status-card">
                <div className="inline-status-label">召回策略</div>
                <div className="inline-status-value">{retrievalModeLabelMap[settings.retrieval.mode] ?? settings.retrieval.mode}</div>
                <div className="inline-status-copy">
                  语义 {settings.retrieval.semantic_weight.toFixed(1)} / 关键词 {settings.retrieval.keyword_weight.toFixed(1)}。
                </div>
              </div>
              <div className="inline-status-card">
                <div className="inline-status-label">上传权限</div>
                <div className="inline-status-value">{canUpload ? '已启用' : '只读'}</div>
                <div className="inline-status-copy">管理员和采购岗可以添加文件并执行切块导入。</div>
              </div>
            </div>
          </section>

          <section className="surface">
            <SectionHeader
              eyebrow="Workspace"
              title="文档与召回测试"
              description="先导入文档，再用当前检索配置验证召回效果。"
              action={(
                <Segmented<ViewMode>
                  value={viewMode}
                  onChange={(value) => setViewMode(value)}
                  options={[
                    { label: '文档中心', value: 'documents' },
                    { label: '召回测试', value: 'retrieval' },
                  ]}
                />
              )}
            />

            {viewMode === 'documents' ? (
              <>
                <div className="toolbar-grid toolbar-grid-documents">
                  <div className="toolbar-field toolbar-field-wide">
                    <span className="toolbar-label">搜索文档</span>
                    <Input value={searchText} onChange={(event) => setSearchText(event.target.value)} prefix={<SearchOutlined />} placeholder="按文件名、来源或分类搜索" />
                  </div>
                  <div className="toolbar-field">
                    <span className="toolbar-label">文档分类</span>
                    <Select value={category} options={categoryOptions} onChange={setCategory} disabled={!canUpload || uploading} />
                  </div>
                  <div className="toolbar-field toolbar-field-wide">
                    <span className="toolbar-label">可见角色</span>
                    <Select mode="multiple" value={allowedRoles} options={roleOptions} onChange={setAllowedRoles} disabled={!canUpload || uploading} />
                  </div>
                  <div className="toolbar-field toolbar-field-actions">
                    <span className="toolbar-label">文件导入</span>
                    <Upload beforeUpload={(file) => handleUpload(file)} showUploadList={false} disabled={!canUpload || uploading}>
                      <Button icon={<UploadOutlined />} type="primary" loading={uploading} disabled={!canUpload} className="button-primary full-width">
                        添加文件
                      </Button>
                    </Upload>
                  </div>
                </div>

                {filteredDocuments.length === 0 && !loadingDocuments ? (
                  <Empty className="empty-state" description="当前没有匹配的文档，请先上传文件或调整搜索条件。" />
                ) : (
                  <div className="table-wrap">
                    <Table
                      rowKey="document_id"
                      loading={loadingDocuments}
                      dataSource={filteredDocuments}
                      pagination={{ pageSize: 8, showSizeChanger: false }}
                      scroll={{ x: 1440 }}
                      className="data-table"
                      columns={columns}
                      expandable={{
                        expandedRowRender: (record) => (
                          <div className="expand-shell">
                            <div className="definition-grid">
                              <div className="definition-item">
                                <div className="definition-label">来源</div>
                                <div className="definition-value">{record.source}</div>
                              </div>
                              <div className="definition-item">
                                <div className="definition-label">版本</div>
                                <div className="definition-value">文档 {record.version} / 图谱 {record.graph_version} / 索引 {record.index_version}</div>
                              </div>
                            </div>
                            <div className="tag-list">
                              {record.allowed_roles.map((role) => (
                                <Tag key={role} className="info-chip">
                                  {roleLabelMap[role] ?? role}
                                </Tag>
                              ))}
                            </div>
                            <div className="audit-block">
                              <strong>处理说明</strong>
                              <p>{record.processing_errors.length > 0 ? record.processing_errors.join('\n') : '当前文档没有处理异常，可以继续用于召回测试和问答。'}</p>
                            </div>
                          </div>
                        ),
                      }}
                    />
                  </div>
                )}
              </>
            ) : (
              <div className="retrieval-test-grid">
                <div className="retrieval-query-panel">
                  <div className="subsection-title">检索配置</div>
                  <div className="tag-list">
                    <Tag className="info-chip">{retrievalModeLabelMap[settings.retrieval.mode] ?? settings.retrieval.mode}</Tag>
                    <Tag className="info-chip">Top K {settings.retrieval.top_k}</Tag>
                    <Tag className="info-chip">阈值 {settings.retrieval.score_threshold_enabled ? settings.retrieval.score_threshold : '关闭'}</Tag>
                  </div>
                  <div className="toolbar-note">召回测试直接复用当前已保存的知识库检索配置。</div>
                  <Input.TextArea
                    value={retrievalQuestion}
                    onChange={(event) => setRetrievalQuestion(event.target.value)}
                    rows={8}
                    maxLength={250}
                    placeholder="输入测试问题，例如：采购标准"
                    className="composer-textarea"
                  />
                  <div className="composer-footer">
                    <div className="composer-hint">{retrievalQuestion.trim().length} / 250</div>
                    <div className="composer-actions">
                      <Button className="button-secondary" onClick={() => {
                        setSettingsOpen(true);
                        setDraftSettings(settings);
                        setPreviewResult(null);
                      }}>
                        调整配置
                      </Button>
                      <Button className="button-primary" type="primary" loading={retrievalTesting} onClick={() => void handleRetrievalTest()}>
                        测试
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="retrieval-results-panel">
                  {retrievalTesting ? (
                    <div className="loading-shell"><Spin size="large" /></div>
                  ) : !retrievalResult ? (
                    <Empty className="empty-state" description="输入查询后即可查看知识库召回到的分块片段。" />
                  ) : retrievalResult.hits.length === 0 ? (
                    <Empty className="empty-state" description="当前查询没有召回到片段，请尝试调整检索或分块设置。" />
                  ) : (
                    <div className="retrieval-result-shell">
                      <div className="retrieval-result-summary">
                        <div className="retrieval-result-count">
                          {retrievalResult.total_hits} 个召回段落
                          <Tag className="info-chip">{retrievalResult.duration_ms}ms</Tag>
                        </div>
                        <div className="panel-note">当前模式：{retrievalModeLabelMap[retrievalResult.mode] ?? retrievalResult.mode}</div>
                      </div>

                      <div className="retrieval-result-list">
                        {retrievalResult.hits.map((item) => (
                          <div key={item.citation} className="retrieval-result-card">
                            <div className="retrieval-result-head">
                              <div>
                                <div className="retrieval-result-title">
                                  {item.chunk_label}
                                  <span>{item.character_count} 字符</span>
                                </div>
                                <div className="retrieval-result-source">来源文件：{item.title}</div>
                              </div>
                              <div className="retrieval-result-actions">
                                <Tag className="score-chip">SCORE {item.score.toFixed(2)}</Tag>
                                <Button size="small" className="button-secondary" onClick={() => {
                                  setViewMode('documents');
                                  setSearchText(item.title);
                                }}>
                                  定位文档
                                </Button>
                              </div>
                            </div>
                            <div className="retrieval-result-snippet">{item.snippet}</div>
                            <div className="retrieval-result-meta">{item.source} · {item.citation}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>

        <aside className="workspace-aside">
          <section className="surface surface-sticky">
            <SectionHeader eyebrow="Knowledge Base Snapshot" title="知识库概览" description="快速判断当前知识库是否处于可导入、可测试状态。" />
            <div className="inspector-list">
              <div className="inspector-card">
                <div className="inspector-label">知识库状态</div>
                <div className="inspector-value">{processingCount > 0 ? '处理中' : '稳定可用'}</div>
                <div className="inspector-copy">{processingCount > 0 ? `当前仍有 ${processingCount} 份文档正在排队或处理中。` : '当前没有积压的导入任务。'}</div>
              </div>
              <div className="inspector-card">
                <div className="inspector-label">分段标识符</div>
                <div className="inspector-value">{settings.chunking.separator}</div>
                <div className="inspector-copy">最大长度 {settings.chunking.max_length}，重叠长度 {settings.chunking.overlap}。</div>
              </div>
              <div className="inspector-card">
                <div className="inspector-label">检索模式</div>
                <div className="inspector-value">{retrievalModeLabelMap[settings.retrieval.mode] ?? settings.retrieval.mode}</div>
                <div className="inspector-copy">阈值{settings.retrieval.score_threshold_enabled ? `已启用（${settings.retrieval.score_threshold}）` : '未启用'}。</div>
              </div>
            </div>
            <div className="resource-group">
              <div className="subsection-title">快速指标</div>
              <div className="tag-list">
                <Tag className="info-chip">{documents.length} 份文档</Tag>
                <Tag className="info-chip">{indexedCount} 份已入库</Tag>
                <Tag className="info-chip">{totalChunks} 个分块</Tag>
                <Tag className="info-chip">{formatBytes(totalStorage)}</Tag>
              </div>
            </div>
          </section>
        </aside>
      </div>

      <Drawer
        title="切块与检索设置"
        placement="right"
        width={520}
        open={settingsOpen}
        onClose={() => {
          setSettingsOpen(false);
          setDraftSettings(settings);
          setPreviewResult(null);
        }}
      >
        <div className="drawer-stack">
          <section className="drawer-section">
            <div className="subsection-title">分段设置</div>
            <div className="settings-grid-3">
              <div className="toolbar-field">
                <span className="toolbar-label">分段标识符</span>
                <Input value={draftSettings.chunking.separator} onChange={(event) => updateDraftChunking('separator', event.target.value)} />
              </div>
              <div className="toolbar-field">
                <span className="toolbar-label">分段最大长度</span>
                <InputNumber min={200} max={4000} value={draftSettings.chunking.max_length} onChange={(value) => updateDraftChunking('max_length', Number(value ?? draftSettings.chunking.max_length))} className="full-width" />
              </div>
              <div className="toolbar-field">
                <span className="toolbar-label">分段重叠长度</span>
                <InputNumber min={0} max={1000} value={draftSettings.chunking.overlap} onChange={(value) => updateDraftChunking('overlap', Number(value ?? draftSettings.chunking.overlap))} className="full-width" />
              </div>
            </div>

            <div className="settings-switch-list">
              <label className="settings-switch-row">
                <span>替换连续空格、换行和制表符</span>
                <Switch checked={draftSettings.chunking.normalize_whitespace} onChange={(checked) => updateDraftChunking('normalize_whitespace', checked)} />
              </label>
              <label className="settings-switch-row">
                <span>移除 URL 和邮箱</span>
                <Switch checked={draftSettings.chunking.strip_urls_emails} onChange={(checked) => updateDraftChunking('strip_urls_emails', checked)} />
              </label>
            </div>
          </section>

          <section className="drawer-section">
            <div className="subsection-title">召回设置</div>
            <div className="toolbar-field">
              <span className="toolbar-label">检索模式</span>
              <Select<QaMode> value={draftSettings.retrieval.mode} options={retrievalModeOptions} onChange={(value) => updateDraftRetrieval('mode', value)} />
            </div>

            <div className="settings-grid-2">
              <div className="toolbar-field">
                <span className="toolbar-label">语义权重</span>
                <Slider min={0} max={1} step={0.05} value={draftSettings.retrieval.semantic_weight} onChange={(value) => updateDraftRetrieval('semantic_weight', Number(value))} />
              </div>
              <div className="toolbar-field">
                <span className="toolbar-label">关键词权重</span>
                <Slider min={0} max={1} step={0.05} value={draftSettings.retrieval.keyword_weight} onChange={(value) => updateDraftRetrieval('keyword_weight', Number(value))} />
              </div>
              <div className="toolbar-field">
                <span className="toolbar-label">Top K</span>
                <InputNumber min={1} max={20} value={draftSettings.retrieval.top_k} onChange={(value) => updateDraftRetrieval('top_k', Number(value ?? draftSettings.retrieval.top_k))} className="full-width" />
              </div>
              <div className="toolbar-field">
                <span className="toolbar-label">Score 阈值</span>
                <div className="threshold-row">
                  <Switch checked={draftSettings.retrieval.score_threshold_enabled} onChange={(checked) => updateDraftRetrieval('score_threshold_enabled', checked)} />
                  <InputNumber min={0} max={5} step={0.1} disabled={!draftSettings.retrieval.score_threshold_enabled} value={draftSettings.retrieval.score_threshold} onChange={(value) => updateDraftRetrieval('score_threshold', Number(value ?? draftSettings.retrieval.score_threshold))} className="full-width" />
                </div>
              </div>
            </div>
          </section>

          <section className="drawer-section">
            <div className="subsection-title">预览切块</div>
            <div className="toolbar-field">
              <span className="toolbar-label">预览文档</span>
              <Select value={previewDocumentId} options={documents.map((item) => ({ label: item.title, value: item.document_id }))} onChange={setPreviewDocumentId} placeholder="选择一个文档" />
            </div>

            <div className="drawer-actions">
              <Button className="button-secondary" onClick={() => void handlePreviewChunks()} loading={previewLoading}>
                预览分块
              </Button>
              <Button className="button-primary" type="primary" onClick={() => void handleSaveSettings()} loading={loadingSettings}>
                保存设置
              </Button>
            </div>

            {previewLoading ? (
              <div className="loading-shell"><Spin /></div>
            ) : previewResult ? (
              <div className="chunk-preview-shell">
                <div className="panel-note">共生成 {previewResult.total_chunks} 个分块，累计 {previewResult.total_characters.toLocaleString('zh-CN')} 字符。</div>
                <div className="chunk-preview-list">
                  {previewResult.chunks.map((item) => (
                    <div key={item.index} className="chunk-preview-card">
                      <div className="chunk-preview-head">
                        <strong>Chunk #{item.index}</strong>
                        <span>{item.character_count} 字符</span>
                      </div>
                      <div className="chunk-preview-content">{item.content}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="panel-note">保存前可以先选中文档预览切块效果。</div>
            )}
          </section>
        </div>
      </Drawer>
    </div>
  );
}
