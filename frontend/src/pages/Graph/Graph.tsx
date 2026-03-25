import { Empty, Tag, message } from 'antd';
import { motion, useReducedMotion } from 'framer-motion';
import { useEffect, useState } from 'react';

import graphApi from '@/api/graphApi';
import GraphVisual from '@/components/GraphVisual/GraphVisual';
import MetricStrip from '@/components/Surface/MetricStrip';
import SectionHeader from '@/components/Surface/SectionHeader';
import type { GraphResponse } from '@/types/graph';

export default function GraphPage() {
  const shouldReduceMotion = useReducedMotion();
  const [graph, setGraph] = useState<GraphResponse | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await graphApi.fetchGraph();
        setGraph(response);
      } catch {
        message.error('图谱数据加载失败，请稍后重试。');
      }
    };

    void load();
  }, []);

  const hasGraph = Boolean(graph && graph.nodes.length > 0);
  const categories = Array.from(new Set(graph?.nodes.map((item) => item.category) ?? []));
  const rankedCommunities = [...(graph?.communities ?? [])].sort(
    (left, right) => right.entity_names.length - left.entity_names.length,
  );

  const metrics = [
    {
      label: '实体节点',
      value: graph?.nodes.length ?? 0,
      detail: '当前图谱中已纳入的实体数量。',
      tone: 'neutral' as const,
    },
    {
      label: '关系边',
      value: graph?.edges.length ?? 0,
      detail: '实体之间可用于推理的关系数量。',
      tone: 'teal' as const,
    },
    {
      label: '来源文档',
      value: graph?.source_documents.length ?? 0,
      detail: '参与建图与检索的文档范围。',
      tone: 'amber' as const,
    },
    {
      label: '主题社区',
      value: graph?.communities.length ?? 0,
      detail: '基于图结构生成的社区摘要数量。',
      tone: 'neutral' as const,
    },
  ];

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

      {!hasGraph ? (
        <section className="surface">
          <SectionHeader
            eyebrow="Relationship Network"
            title="知识图谱视图"
            description="当前图谱为空，请先上传并入库文档，系统才会生成可浏览的实体关系。"
          />
          <Empty className="empty-state" description="当前没有可视化图谱数据。" />
        </section>
      ) : (
        <div className="workspace-grid workspace-grid-graph">
          <section className="surface surface-strong">
            <SectionHeader
              eyebrow="Relationship Network"
              title="关系网络"
              description="Local、Global 与 Hybrid 模式都会复用这里的图结构与社区信息。"
              meta={`分类 ${categories.length} 类`}
            />

            <div className="legend-row">
              {categories.map((category) => (
                <Tag key={category} className="info-chip">
                  {category}
                </Tag>
              ))}
            </div>

            <GraphVisual graph={graph as GraphResponse} />
          </section>

          <motion.aside className="workspace-aside" {...asideMotion}>
            <section className="surface surface-sticky">
              <SectionHeader
                eyebrow="Community Summary"
                title="社区摘要"
                description="优先展示规模较大的主题社区，帮助快速定位知识热点。"
              />

              <div className="community-list">
                {rankedCommunities.slice(0, 6).map((community) => (
                  <div key={community.community_id} className="community-item">
                    <div className="community-header">
                      <div>
                        <div className="community-title">{community.name}</div>
                        <div className="community-meta">
                          {community.category} · {community.entity_names.length} 个实体
                        </div>
                      </div>
                      <Tag className="info-chip">{community.source_documents.length} 份文档</Tag>
                    </div>
                    <div className="community-summary">{community.summary || '当前社区尚未生成摘要。'}</div>
                  </div>
                ))}
              </div>

              <div className="resource-group">
                <div className="subsection-title">邻居关系</div>
                <div className="tag-list">
                  {Object.entries(graph?.entity_neighbors ?? {})
                    .slice(0, 10)
                    .map(([source, targets]) => (
                      <span key={source} className="resource-chip">
                        {source} → {targets.slice(0, 2).join(' / ')}
                      </span>
                    ))}
                </div>
              </div>
            </section>
          </motion.aside>
        </div>
      )}
    </div>
  );
}
