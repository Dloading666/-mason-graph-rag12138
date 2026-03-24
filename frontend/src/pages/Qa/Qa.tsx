import { BugOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { Button, Collapse, Empty, List, Select, Spin, Tag, Typography, message } from 'antd';
import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';

import platformApi from '@/api/platformApi';
import qaApi from '@/api/qaApi';
import EvidencePanel from '@/components/EvidencePanel/EvidencePanel';
import QuestionInput from '@/components/QuestionInput/QuestionInput';
import type { ConversationMessage, QaMode, QaResponse, QaStreamEvent } from '@/types/qa';

const { Paragraph } = Typography;

type InteractionMode = 'standard' | 'stream' | 'debug';

const QUICK_QUESTIONS = [
  '抗裂砂浆施工规范和国标要求有哪些？',
  '外墙保温系统常见质量问题有哪些？',
  '墙面开裂如何排查并选择修复材料？',
  '采购审批流程里超过 5 万元的要求是什么？',
];

const MODE_OPTIONS: Array<{ label: string; value: QaMode }> = [
  { label: '自动（按问题复杂度自动选择）', value: 'auto' },
  { label: 'Naive（只看文档片段）', value: 'naive' },
  { label: 'Local Graph（实体邻居检索）', value: 'local' },
  { label: 'Global（社区摘要检索）', value: 'global' },
  { label: 'Hybrid（文档 + 图谱混合）', value: 'hybrid' },
  { label: 'Fusion（规划推理长答）', value: 'fusion' },
];

const MODE_LABELS: Record<string, string> = Object.fromEntries(
  MODE_OPTIONS.map((item) => [item.value, item.label]),
);

const INTERACTION_MODE_LABELS: Record<InteractionMode, string> = {
  standard: '标准回答',
  stream: '流式响应',
  debug: '调试模式',
};

const STREAM_STAGE_LABELS: Record<string, string> = {
  retrieving: '正在检索知识库证据，并等待流式结果...',
};

const EMPTY_ANSWER_FALLBACK = '系统已完成检索，但当前没有生成答案，请先查看证据链并稍后重试。';

function formatElapsedTime(elapsedSeconds: number) {
  const safeSeconds = Math.max(0, elapsedSeconds);
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;

  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function buildConversationMessage(question: string, response: QaResponse): ConversationMessage {
  return {
    id: response.trace_id,
    traceId: response.trace_id,
    question,
    answer: response.answer?.trim() || EMPTY_ANSWER_FALLBACK,
    evidence: response.evidence ?? [],
    citations: response.citations ?? [],
    mode: response.mode,
    plan: response.plan ?? null,
    executionSummary: response.execution_summary ?? null,
    debug: response.debug ?? null,
    createdAt: new Date().toISOString(),
  };
}

interface ThinkingStatusProps {
  label: string;
  description: string;
  elapsedSeconds: number;
  className?: string;
}

function ThinkingStatus({ label, description, elapsedSeconds, className }: ThinkingStatusProps) {
  return (
    <div className={['thinking-status', className].filter(Boolean).join(' ')} role="status" aria-live="polite">
      <Spin size="large" />
      <div className="thinking-status-copy">
        <div className="thinking-status-line">
          <span className="thinking-status-label">{label}</span>
          <span className="thinking-status-timer">{formatElapsedTime(elapsedSeconds)}</span>
        </div>
        <div className="thinking-status-hint">{description}</div>
      </div>
    </div>
  );
}

export default function QaPage() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [requestStartedAt, setRequestStartedAt] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [streamStage, setStreamStage] = useState<string | null>(null);
  const [interactionMode, setInteractionMode] = useState<InteractionMode>('standard');
  const [mode, setMode] = useState<QaMode>('auto');
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  const latestMessage = messages[0];
  const isBusy = loading || reportLoading;

  const activeRequestLabel = reportLoading
    ? '报告生成中'
    : interactionMode === 'stream'
      ? '流式响应中'
      : interactionMode === 'debug'
        ? '调试分析中'
        : '思考中';

  const activeRequestDescription = reportLoading
    ? '正在生成长报告，请稍候...'
    : interactionMode === 'stream'
      ? STREAM_STAGE_LABELS[streamStage ?? ''] ?? '已连接流式通道，正在等待服务端返回事件...'
      : interactionMode === 'debug'
        ? '正在生成答案，并附带计划、执行摘要和调试信息...'
        : '正在检索知识库并生成回答...';

  const statusCards = [
    {
      label: '回答记录',
      value: String(messages.length).padStart(2, '0'),
      note: '最近的问题与答案会按时间倒序保留，便于复盘。',
    },
    {
      label: '当前检索',
      value: MODE_LABELS[mode] ?? mode,
      note: '切换不同检索模式，可以观察证据命中差异。',
    },
    {
      label: '回答方式',
      value: INTERACTION_MODE_LABELS[interactionMode],
      note: '流式响应与调试模式互斥，再点一次当前按钮可回到标准回答。',
    },
    {
      label: '最新引用',
      value: String(latestMessage?.citations.length ?? 0),
      note: '显示上一条回答附带的引用数量。',
    },
  ];

  const appendMessage = (messageItem: ConversationMessage) => {
    setMessages((current) => [messageItem, ...current]);
  };

  useEffect(() => {
    if (requestStartedAt === null) {
      return;
    }

    const updateElapsedSeconds = () => {
      setElapsedSeconds(Math.floor((Date.now() - requestStartedAt) / 1000));
    };

    updateElapsedSeconds();
    const timer = window.setInterval(updateElapsedSeconds, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [requestStartedAt]);

  const startRequestTimer = () => {
    setElapsedSeconds(0);
    setRequestStartedAt(Date.now());
  };

  const stopRequestTimer = () => {
    setElapsedSeconds(0);
    setRequestStartedAt(null);
    setStreamStage(null);
  };

  const toggleInteractionMode = (nextMode: Exclude<InteractionMode, 'standard'>) => {
    setInteractionMode((current) => (current === nextMode ? 'standard' : nextMode));
  };

  const handleStreamEvent = (trimmedQuestion: string) => (event: QaStreamEvent) => {
    if (event.type === 'stage') {
      setStreamStage(event.data.stage);
      return;
    }

    if (event.type === 'answer') {
      appendMessage(buildConversationMessage(trimmedQuestion, event.data));
      setQuestion('');
      return;
    }

    if (event.type === 'done') {
      setStreamStage(event.data.status);
    }
  };

  const handleSend = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isBusy) {
      return;
    }

    setLoading(true);
    startRequestTimer();

    try {
      if (interactionMode === 'stream') {
        await qaApi.askQuestionStream(
          {
            question: trimmedQuestion,
            need_evidence: true,
            mode,
            debug: false,
          },
          { onEvent: handleStreamEvent(trimmedQuestion) },
        );
      } else {
        const response = await qaApi.askQuestion({
          question: trimmedQuestion,
          need_evidence: true,
          mode,
          debug: interactionMode === 'debug',
        });

        appendMessage(buildConversationMessage(trimmedQuestion, response));
        setQuestion('');
      }
    } catch {
      message.error(interactionMode === 'stream' ? '流式问答失败，请稍后重试。' : '问答失败，请检查后端服务或稍后重试。');
    } finally {
      setLoading(false);
      stopRequestTimer();
    }
  };

  const handleResearchReport = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isBusy) {
      return;
    }

    setReportLoading(true);
    startRequestTimer();
    const toastKey = `research-${Date.now()}`;
    message.loading({ content: '正在生成长报告，请稍候...', key: toastKey, duration: 0 });

    try {
      const job = await platformApi.createResearchReport(trimmedQuestion, 'fusion');
      for (let attempt = 0; attempt < 15; attempt += 1) {
        const snapshot = await platformApi.getJob(job.job_id);
        if (snapshot.status === 'completed' && snapshot.result) {
          appendMessage({
            id: snapshot.job_id,
            traceId: snapshot.result.trace_id ?? snapshot.job_id,
            question: trimmedQuestion,
            answer: snapshot.result.answer?.trim() || EMPTY_ANSWER_FALLBACK,
            evidence: [],
            citations: snapshot.result.citations ?? [],
            mode: snapshot.result.mode ?? 'fusion',
            plan: snapshot.result.plan ?? null,
            executionSummary: snapshot.result.execution_summary ?? null,
            debug: null,
            createdAt: new Date().toISOString(),
          });
          setQuestion('');
          message.success({ content: '长报告已生成。', key: toastKey });
          return;
        }

        if (snapshot.status === 'failed') {
          throw new Error(snapshot.error_message ?? '报告生成失败');
        }

        await new Promise((resolve) => {
          window.setTimeout(resolve, 1500);
        });
      }

      message.warning({ content: '报告任务仍在执行，可稍后到任务中心查看。', key: toastKey });
    } catch {
      message.error({ content: '长报告生成失败，请稍后重试。', key: toastKey });
    } finally {
      setReportLoading(false);
      stopRequestTimer();
    }
  };

  const handleFeedback = async (traceId: string, sentiment: 'positive' | 'negative') => {
    try {
      await platformApi.submitFeedback({
        trace_id: traceId,
        rating: sentiment === 'positive' ? 5 : 2,
        sentiment,
      });
      message.success('反馈已提交。');
    } catch {
      message.error('反馈提交失败。');
    }
  };

  return (
    <div className="workspace-stack">
      <section className="page-hero">
        <div>
          <div className="page-kicker">Question Workspace</div>
          <h1 className="page-title">建材智能问答</h1>
          <p className="page-subtitle">
            围绕施工规范、材料参数和采购制度发问，系统会优先返回可核验的证据与引用。
          </p>
          <div className="chip-cluster" style={{ marginTop: 18 }}>
            <Tag className="utility-chip">Qwen3.5-plus</Tag>
            <Tag className="utility-chip">GraphRAG Core</Tag>
            <Tag className="utility-chip">{INTERACTION_MODE_LABELS[interactionMode]}</Tag>
          </div>
        </div>

        <div className="hero-stat-grid">
          {statusCards.map((item) => (
            <div key={item.label} className="hero-stat">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              <div className="metric-note" style={{ color: 'rgba(228, 236, 242, 0.68)' }}>
                {item.note}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="workspace-grid">
        <div className="panel-surface panel-emphasis">
          <div className="panel-heading">
            <div>
              <div className="section-eyebrow">Retrieval Setup</div>
              <h2 className="panel-title">提问与证据返回</h2>
              <p className="panel-description">先选择检索模式，再选择回答方式。流式响应与调试模式互斥，方便你清楚区分当前链路。</p>
            </div>
            <div className="panel-meta">Trace 优先</div>
          </div>

          <div className="toolbar-grid toolbar-grid-qa">
            <div className="field-stack">
              <span className="field-label">检索模式</span>
              <Select<QaMode> value={mode} options={MODE_OPTIONS} onChange={setMode} disabled={isBusy} />
            </div>

            <div className="field-stack">
              <span className="field-label">回答方式</span>
              <div className="mode-toggle-row">
                <Button
                  size="large"
                  icon={<ThunderboltOutlined />}
                  disabled={isBusy}
                  onClick={() => toggleInteractionMode('stream')}
                  className={`mode-toggle-button ${interactionMode === 'stream' ? 'mode-toggle-button-active' : ''}`}
                >
                  流式响应
                </Button>
                <Button
                  size="large"
                  icon={<BugOutlined />}
                  disabled={isBusy}
                  onClick={() => toggleInteractionMode('debug')}
                  className={`mode-toggle-button ${interactionMode === 'debug' ? 'mode-toggle-button-active' : ''}`}
                >
                  调试模式
                </Button>
              </div>
              <div className="mode-toggle-note">启动一种模式会自动禁用另一种模式，再点一次当前按钮可回到标准回答。</div>
            </div>
          </div>

          {isBusy ? (
            <div className="composer-status-slot">
              <ThinkingStatus
                label={activeRequestLabel}
                description={activeRequestDescription}
                elapsedSeconds={elapsedSeconds}
                className="thinking-status-wide"
              />
            </div>
          ) : null}

          <QuestionInput
            value={question}
            loading={isBusy}
            onChange={setQuestion}
            onSend={handleSend}
            onClear={() => setQuestion('')}
          />

          <div className="chip-cluster">
            {QUICK_QUESTIONS.map((item) => (
              <Button key={item} className="quick-question" onClick={() => setQuestion(item)} disabled={isBusy}>
                {item}
              </Button>
            ))}
          </div>
        </div>

        <aside className="panel-surface panel-side">
          <div className="panel-heading">
            <div>
              <div className="section-eyebrow">Operation Status</div>
              <h2 className="panel-title panel-title-sm">运行面板</h2>
            </div>
          </div>

          <div className="signal-stack">
            <div className="signal-card">
              <div className="signal-mini-label">当前检索</div>
              <div className="signal-mini-value">{MODE_LABELS[mode] ?? mode}</div>
              <div className="signal-mini-copy">不同模式会影响证据召回范围和推理方式。</div>
            </div>
            <div className="signal-card">
              <div className="signal-mini-label">回答方式</div>
              <div className="signal-mini-value">{INTERACTION_MODE_LABELS[interactionMode]}</div>
              <div className="signal-mini-copy">流式响应更快反馈阶段状态，调试模式会附带计划和调试信息。</div>
            </div>
            <div className="signal-card">
              <div className="signal-mini-label">最近 Trace</div>
              <div className="signal-mini-value">{latestMessage?.traceId.slice(0, 8) ?? '尚未生成'}</div>
              <div className="signal-mini-copy">每次回答都会记录 Trace，方便审计和复核。</div>
            </div>
          </div>

          <Button
            onClick={handleResearchReport}
            loading={reportLoading}
            disabled={!question.trim() || isBusy}
            className="secondary-button full-width"
          >
            生成长报告
          </Button>
          <div className="aside-note">长报告默认使用 Fusion 模式，会以异步任务形式生成并回写到当前记录区。</div>
        </aside>
      </section>

      <section className="panel-surface">
        <div className="panel-heading">
          <div>
            <div className="section-eyebrow">Trace Archive</div>
            <h2 className="panel-title">回答记录</h2>
            <p className="panel-description">按时间倒序展示问题、回答、引用、证据链和调试信息。</p>
          </div>
          <div className="panel-meta">最近 Trace: {latestMessage?.traceId ?? '尚未生成'}</div>
        </div>

        {isBusy ? (
          <div className="loading-shell">
            <ThinkingStatus
              label={activeRequestLabel}
              description={activeRequestDescription}
              elapsedSeconds={elapsedSeconds}
              className="thinking-status-center"
            />
          </div>
        ) : messages.length === 0 ? (
          <Empty
            description="请输入建材相关问题，例如：抗裂砂浆施工规范、水泥型号参数、采购审批流程。"
            className="embedded-empty"
          />
        ) : (
          <List
            split={false}
            className="message-list"
            dataSource={messages}
            renderItem={(item) => {
              const detailItems: Array<{ key: string; label: string; children: ReactNode }> = [];

              if (item.plan || item.executionSummary) {
                detailItems.push({
                  key: `${item.id}-plan`,
                  label: '计划与执行',
                  children: (
                    <pre className="json-block">
                      {JSON.stringify(
                        {
                          plan: item.plan,
                          executionSummary: item.executionSummary,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  ),
                });
              }

              if (item.debug) {
                detailItems.push({
                  key: `${item.id}-debug`,
                  label: '调试信息',
                  children: <pre className="json-block">{JSON.stringify(item.debug, null, 2)}</pre>,
                });
              }

              return (
                <List.Item key={item.id} className="message-card">
                  <div className="message-header">
                    <div style={{ flex: 1 }}>
                      <div className="message-label">问题</div>
                      <Paragraph className="message-question">{item.question}</Paragraph>
                    </div>
                    <div className="message-tags">
                      <Tag className="utility-chip">{MODE_LABELS[item.mode] ?? item.mode}</Tag>
                      <Tag className="utility-chip">Trace: {item.traceId}</Tag>
                    </div>
                  </div>

                  <div>
                    <div className="message-label">回答</div>
                    <Paragraph className="message-answer">{item.answer || EMPTY_ANSWER_FALLBACK}</Paragraph>
                  </div>

                  <div className="chip-cluster">
                    {item.citations.map((citation) => (
                      <Tag key={citation} className="citation-chip">
                        {citation}
                      </Tag>
                    ))}
                  </div>

                  <div className="feedback-row">
                    <Button className="feedback-button" size="small" onClick={() => handleFeedback(item.traceId, 'positive')}>
                      有帮助
                    </Button>
                    <Button className="feedback-button" size="small" onClick={() => handleFeedback(item.traceId, 'negative')}>
                      需改进
                    </Button>
                  </div>

                  <EvidencePanel evidence={item.evidence} />

                  {detailItems.length > 0 ? <Collapse className="detail-collapse" items={detailItems} /> : null}
                </List.Item>
              );
            }}
          />
        )}
      </section>
    </div>
  );
}
