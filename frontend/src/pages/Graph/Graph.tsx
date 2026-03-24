import { Empty, Tag, message } from 'antd';
import { useEffect, useState } from 'react';

import graphApi from '@/api/graphApi';
import GraphVisual from '@/components/GraphVisual/GraphVisual';
import type { GraphResponse } from '@/types/graph';

export default function GraphPage() {
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

  const stats = hasGraph
    ? [
        {
          label: '节点数',
          value: graph?.nodes.length ?? 0,
          note: '当前知识图谱中已入库的实体总数。',
        },
        {
          label: '关系数',
          value: graph?.edges.length ?? 0,
          note: '实体之间可用于推理的关系数量。',
        },
        {
          label: '来源文档数',
          value: graph?.source_documents.length ?? 0,
          note: '已参与建图和检索的文档数量。',
        },
        {
          label: '社区数',
          value: graph?.communities.length ?? 0,
          note: '由分类和产品聚合生成的图谱社区数量。',
        },
      ]
    : [];

  return (
    <div className="workspace-stack">
      <section className="page-hero">
        <div>
          <div className="page-kicker">Graph Insight</div>
          <h1 className="page-title">知识图谱关系视图</h1>
          <p className="page-subtitle">
            当前图查询优先读取 Neo4j。社区摘要、邻居扩展和路径推理结果会与问答主链路保持一致。
          </p>
          <div className="chip-cluster" style={{ marginTop: 18 }}>
            {categories.length > 0 ? (
              categories.slice(0, 6).map((item) => (
                <Tag key={item} className="utility-chip">
                  {item}
                </Tag>
              ))
            ) : (
              <Tag className="utility-chip">等待图谱入库</Tag>
            )}
          </div>
        </div>

        <div className="hero-stat-grid">
          <div className="hero-stat">
            <span>图谱状态</span>
            <strong>{hasGraph ? '在线' : '空图'}</strong>
            <div className="metric-note" style={{ color: 'rgba(228, 236, 242, 0.68)' }}>
              先上传并入库文档，系统才会生成可浏览的实体关系。
            </div>
          </div>
          <div className="hero-stat">
            <span>社区摘要</span>
            <strong>{rankedCommunities.length}</strong>
            <div className="metric-note" style={{ color: 'rgba(228, 236, 242, 0.68)' }}>
              社区结果已纳入 global 和 hybrid 检索路径。
            </div>
          </div>
        </div>
      </section>

      {!hasGraph ? (
        <section className="panel-surface">
          <Empty
            className="embedded-empty"
            description="当前可视化图谱为空，请先上传并入库建材文档。"
          />
        </section>
      ) : (
        <>
          <section className="metric-grid">
            {stats.map((item) => (
              <div key={item.label} className="metric-tile">
                <div className="metric-label">{item.label}</div>
                <div className="metric-value">{item.value}</div>
                <div className="metric-note">{item.note}</div>
              </div>
            ))}
          </section>

          <section className="graph-layout">
            <div className="panel-surface graph-stage">
              <div className="panel-heading">
                <div>
                  <div className="section-eyebrow">Relationship Network</div>
                  <h2 className="panel-title">知识图谱可视化</h2>
                  <p className="panel-description">
                    local、global 和 hybrid 模式都会优先复用这里的图结构与社区结果。
                  </p>
                </div>
                <div className="panel-meta">分类 {categories.length} 种</div>
              </div>
              <GraphVisual graph={graph as GraphResponse} />
            </div>

            <aside className="panel-surface panel-side">
              <div>
                <div className="section-eyebrow">Community Summary</div>
                <h2 className="panel-title panel-title-sm">主题社区</h2>
                <p className="panel-description">
                  优先展示实体规模较大的社区，方便快速定位建材知识主题。
                </p>
              </div>

              <div className="community-list">
                {rankedCommunities.slice(0, 6).map((community) => (
                  <div key={community.community_id} className="community-card">
                    <div className="community-header">
                      <div>
                        <div className="community-title">{community.name}</div>
                        <div className="community-meta">
                          {community.category} / {community.entity_names.length} 个实体
                        </div>
                      </div>
                      <Tag className="utility-chip">{community.source_documents.length} 份文档</Tag>
                    </div>
                    <div className="community-summary">
                      {community.summary || '当前社区暂未生成摘要。'}
                    </div>
                  </div>
                ))}
              </div>

              <div className="resource-list">
                <div className="section-eyebrow">Entity Neighbors</div>
                <div className="chip-cluster" style={{ marginTop: 12 }}>
                  {Object.entries(graph?.entity_neighbors ?? {})
                    .slice(0, 8)
                    .map(([source, targets]) => (
                      <span key={source} className="resource-chip">
                        {source}
                        {' -> '}
                        {targets.slice(0, 2).join(' / ')}
                      </span>
                    ))}
                </div>
              </div>
            </aside>
          </section>
        </>
      )}
    </div>
  );
}
