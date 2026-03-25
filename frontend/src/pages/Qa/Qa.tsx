import { BugOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { Button, Collapse, Empty, Select, Spin, Tag, Typography, message } from 'antd';
import { motion, useReducedMotion } from 'framer-motion';
import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';

import platformApi from '@/api/platformApi';
import qaApi from '@/api/qaApi';
import EvidencePanel from '@/components/EvidencePanel/EvidencePanel';
import QuestionInput from '@/components/QuestionInput/QuestionInput';
import MetricStrip from '@/components/Surface/MetricStrip';
import SectionHeader from '@/components/Surface/SectionHeader';
import type { ConversationMessage, QaMode, QaResponse, QaStreamEvent } from '@/types/qa';
import { formatDateTime } from '@/utils/format';

const { Paragraph } = Typography;

type InteractionMode = 'standard' | 'stream' | 'debug';

const QUICK_QUESTIONS = [
  '抗裂砂浆施工规范有哪些关键要求？',
  '外墙保温系统常见质量问题有哪些？',
  '墙面开裂时应该如何排查并选择修复材料？',
  '采购审批流程里超 5 万元的要求是什么？',
];

const MODE_OPTIONS: Array<{ label: string; value: QaMode }> = [
  { label: '自动选择', value: 'auto' },
  { label: 'Naive 文档检索', value: 'naive' },
  { label: 'Local Graph 邻居检索', value: 'local' },
  { label: 'Global 社区检索', value: 'global' },
  { label: 'Hybrid 混合检索', value: 'hybrid' },
  { label: 'Fusion 深度回答', value: 'fusion' },
];

const MODE_LABELS: Record<string, string> = Object.fromEntries(MODE_OPTIONS.map((item) => [item.value, item.label]));

const INTERACTION_MODE_LABELS: Record<InteractionMode, string> = {
  standard: '标准回答',
  stream: '流式响应',
  debug: '调试模式',
};

const STREAM_STAGE_LABELS: Record<string, string> = {
  retrieving: '正在检索证据、邻居关系与社区摘要...',
};

const EMPTY_ANSWER_FALLBACK = '系统已完成检索，但当前没有生成可展示的答案，请先查看证据链后稍后重试。';

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
}

function ThinkingStatus({ label, description, elapsedSeconds }: ThinkingStatusProps) {
  return (
    <div className="thinking-status" role="status" aria-live="polite">
      <Spin size="large" />
      <div className="thinking-status-copy">
        <div className="thinking-status-row">
          <span className="thinking-status-label">{label}</span>
          <span className="thinking-status-timer">{formatElapsedTime(elapsedSeconds)}</span>
        </div>
        <div className="thinking-status-note">{description}</div>
      </div>
    </div>
  );
}

export default function QaPage() {
  const shouldReduceMotion = useReducedMotion();
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
    ? '生成研究报告'
    : interactionMode === 'stream'
      ? '流式响应中'
      : interactionMode === 'debug'
        ? '调试分析中'
        : '检索与回答中';

  const activeRequestDescription = reportLoading
    ? '系统正在以异步任务方式生成长报告，请稍候。'
    : interactionMode === 'stream'
      ? STREAM_STAGE_LABELS[streamStage ?? ''] ?? '已连接流式通道，正在等待服务端事件。'
      : interactionMode === 'debug'
        ? '当前会返回答案，同时附带计划、执行摘要和调试信息。'
        : '系统正在检索知识库、图谱与证据并生成回答。';

  const metrics = [
    {
      label: '会话记录',
      value: String(messages.length).padStart(2, '0'),
      detail: '当前浏览器会话中已保存的回答条目。',
      tone: 'neutral' as const,
    },
    {
      label: '当前检索',
      value: MODE_LABELS[mode] ?? mode,
      detail: '决定证据召回范围与推理路径。',
      tone: 'teal' as const,
    },
    {
      label: '回答方式',
      value: INTERACTION_MODE_LABELS[interactionMode],
      detail: '标准、流式和调试三种方式可随时切换。',
      tone: 'amber' as const,
    },
    {
      label: '最新引用',
      value: latestMessage?.citations.length ?? 0,
      detail: '最近一条回答返回的引用数量。',
      tone: 'neutral' as const,
    },
  ];

  const inspectorRows = [
    {
      label: '当前检索模式',
      value: MODE_LABELS[mode] ?? mode,
      note: '切换后会影响召回范围、证据质量与回答节奏。',
    },
    {
      label: '当前回答方式',
      value: INTERACTION_MODE_LABELS[interactionMode],
      note: '调试模式会额外返回计划与执行摘要。',
    },
    {
      label: '最新 Trace',
      value: latestMessage?.traceId ?? '尚未生成',
      note: '每次回答都会记录 Trace，便于审计与复盘。',
    },
    {
      label: '最近更新时间',
      value: latestMessage ? formatDateTime(latestMessage.createdAt) : '--',
      note: '当前面板会优先显示最近一条回答的状态。',
    },
  ];

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

  const appendMessage = (messageItem: ConversationMessage) => {
    setMessages((current) => [messageItem, ...current]);
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
    message.loading({ content: '正在生成研究报告，请稍候...', key: toastKey, duration: 0 });

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
          message.success({ content: '研究报告已生成。', key: toastKey });
          return;
        }

        if (snapshot.status === 'failed') {
          throw new Error(snapshot.error_message ?? '研究报告生成失败');
        }

        await new Promise((resolve) => {
          window.setTimeout(resolve, 1500);
        });
      }

      message.warning({ content: '报告任务仍在执行，可稍后到任务中心查看。', key: toastKey });
    } catch {
      message.error({ content: '研究报告生成失败，请稍后重试。', key: toastKey });
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
      message.success('反馈已提交');
    } catch {
      message.error('反馈提交失败');
    }
  };

  const asideMotion = shouldReduceMotion
    ? {}
    : {
        initial: { opacity: 0, x: 18 },
        animate: { opacity: 1, x: 0 },
        transition: { duration: 0.34, delay: 0.08 },
      };

  return (
    <div className="workspace-page">
      <MetricStrip items={metrics} />

      <div className="workspace-grid workspace-grid-qa">
        <div className="workspace-main-column">
          <section className="surface surface-strong">
            <SectionHeader
              eyebrow="Retrieval Setup"
              title="提问与检索设置"
              description="先选择检索模式，再决定回答方式。输入区、记录区和证据面板保持统一的审计视角。"
              meta="Trace 优先"
            />

            <div className="toolbar-grid">
              <div className="toolbar-field">
                <span className="toolbar-label">检索模式</span>
                <Select<QaMode> value={mode} options={MODE_OPTIONS} onChange={setMode} disabled={isBusy} />
              </div>

              <div className="toolbar-field toolbar-field-wide">
                <span className="toolbar-label">回答方式</span>
                <div className="toggle-row">
                  <Button
                    size="large"
                    icon={<ThunderboltOutlined />}
                    disabled={isBusy}
                    onClick={() => toggleInteractionMode('stream')}
                    className={`button-secondary ${interactionMode === 'stream' ? 'toggle-button-active' : ''}`}
                  >
                    流式响应
                  </Button>
                  <Button
                    size="large"
                    icon={<BugOutlined />}
                    disabled={isBusy}
                    onClick={() => toggleInteractionMode('debug')}
                    className={`button-secondary ${interactionMode === 'debug' ? 'toggle-button-active' : ''}`}
                  >
                    调试模式
                  </Button>
                </div>
                <div className="toolbar-note">再次点击当前按钮可恢复到标准回答。</div>
              </div>
            </div>

            {isBusy ? (
              <div className="status-block">
                <ThinkingStatus
                  label={activeRequestLabel}
                  description={activeRequestDescription}
                  elapsedSeconds={elapsedSeconds}
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

            <div className="quick-list">
              {QUICK_QUESTIONS.map((item) => (
                <Button key={item} className="button-secondary quick-question" onClick={() => setQuestion(item)} disabled={isBusy}>
                  {item}
                </Button>
              ))}
            </div>
          </section>

          <section className="surface">
            <SectionHeader
              eyebrow="Trace Archive"
              title="回答记录"
              description="按时间倒序查看问题、答案、引用、证据链和调试信息。"
              meta={latestMessage ? `最新 Trace: ${latestMessage.traceId}` : '等待首条回答'}
            />

            {isBusy && messages.length === 0 ? (
              <div className="loading-shell">
                <ThinkingStatus
                  label={activeRequestLabel}
                  description={activeRequestDescription}
                  elapsedSeconds={elapsedSeconds}
                />
              </div>
            ) : messages.length === 0 ? (
              <Empty description="请输入建材相关问题，例如规范条文、参数要求或采购制度。" className="empty-state" />
            ) : (
              <div className="answer-log">
                {messages.map((item) => {
                  const detailItems: Array<{ key: string; label: string; children: ReactNode }> = [];

                  if (item.plan || item.executionSummary) {
                    detailItems.push({
                      key: `${item.id}-plan`,
                      label: '计划与执行摘要',
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
                    <div key={item.id} className="answer-entry">
                      <div className="entry-head">
                        <div className="entry-head-copy">
                          <div className="entry-label">问题</div>
                          <Paragraph className="entry-question">{item.question}</Paragraph>
                        </div>
                        <div className="entry-tags">
                          <Tag className="info-chip">{MODE_LABELS[item.mode] ?? item.mode}</Tag>
                          <Tag className="info-chip">{formatDateTime(item.createdAt)}</Tag>
                        </div>
                      </div>

                      <div className="entry-section">
                        <div className="entry-label">回答</div>
                        <Paragraph className="entry-answer">{item.answer || EMPTY_ANSWER_FALLBACK}</Paragraph>
                      </div>

                      <div className="tag-list">
                        {item.citations.map((citation) => (
                          <Tag key={citation} className="info-chip">
                            {citation}
                          </Tag>
                        ))}
                      </div>

                      <div className="feedback-row">
                        <Button className="button-secondary feedback-button" size="small" onClick={() => handleFeedback(item.traceId, 'positive')}>
                          有帮助
                        </Button>
                        <Button className="button-secondary feedback-button" size="small" onClick={() => handleFeedback(item.traceId, 'negative')}>
                          需改进
                        </Button>
                      </div>

                      <EvidencePanel evidence={item.evidence} />

                      {detailItems.length > 0 ? <Collapse className="detail-collapse" items={detailItems} /> : null}
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>

        <motion.aside className="workspace-aside" {...asideMotion}>
          <section className="surface surface-sticky">
            <SectionHeader
              eyebrow="Operation Status"
              title="运行面板"
              description="跟踪当前回答方式、报告生成入口和最近一次 Trace。"
            />

            <div className="inspector-list">
              {inspectorRows.map((item) => (
                <div key={item.label} className="inspector-card">
                  <div className="inspector-label">{item.label}</div>
                  <div className="inspector-value">{item.value}</div>
                  <div className="inspector-copy">{item.note}</div>
                </div>
              ))}
            </div>

            <Button
              onClick={handleResearchReport}
              loading={reportLoading}
              disabled={!question.trim() || isBusy}
              className="button-primary full-width"
            >
              生成研究报告
            </Button>

            <div className="panel-note">研究报告默认使用 Fusion 模式，以异步任务形式生成，可在任务中心继续跟踪。</div>
          </section>
        </motion.aside>
      </div>
    </div>
  );
}
