import ReactECharts from 'echarts-for-react';

import type { GraphResponse } from '@/types/graph';

interface GraphVisualProps {
  graph: GraphResponse;
}

export default function GraphVisual({ graph }: GraphVisualProps) {
  const palette = ['#60a5fa', '#38bdf8', '#2563eb', '#1d4ed8', '#0ea5e9', '#93c5fd'];
  const categories = Array.from(new Set(graph.nodes.map((node) => node.category)));
  const degrees = graph.edges.reduce<Record<string, number>>((accumulator, edge) => {
    accumulator[edge.source] = (accumulator[edge.source] ?? 0) + 1;
    accumulator[edge.target] = (accumulator[edge.target] ?? 0) + 1;
    return accumulator;
  }, {});
  const categoryColorMap = categories.reduce<Record<string, string>>((accumulator, category, index) => {
    accumulator[category] = palette[index % palette.length];
    return accumulator;
  }, {});

  const option = {
    backgroundColor: 'transparent',
    animationDuration: 760,
    animationDurationUpdate: 420,
    tooltip: {
      backgroundColor: 'rgba(8, 22, 30, 0.96)',
      borderWidth: 0,
      padding: 12,
      textStyle: {
        color: '#dce8ff',
      },
      formatter: (params: { dataType: string; data: any }) => {
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/>关系：${params.data.relation}`;
        }

        return `${params.data.name}<br/>分类：${params.data.category}<br/>连接数：${params.data.degree}<br/>来源文档：${params.data.documentCount}`;
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        scaleLimit: { min: 0.55, max: 2.4 },
        label: {
          show: true,
          position: 'right',
          color: '#e1ebff',
          fontSize: 11,
        },
        force: {
          repulsion: 340,
          edgeLength: [92, 180],
          gravity: 0.08,
        },
        lineStyle: {
          color: 'rgba(157, 184, 230, 0.34)',
          width: 1.4,
          curveness: 0.16,
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 6],
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 2.3,
          },
        },
        categories: categories.map((item) => ({ name: item })),
        data: graph.nodes.map((node) => ({
          id: node.id,
          name: node.name,
          category: node.category,
          degree: degrees[node.id] ?? 0,
          documentCount: node.source_documents.length,
          value: degrees[node.id] ?? 0,
          symbolSize: Math.min(42, 18 + (degrees[node.id] ?? 0) * 2 + node.source_documents.length),
          itemStyle: {
            color: categoryColorMap[node.category],
            borderColor: 'rgba(229, 238, 255, 0.9)',
            borderWidth: 1.6,
            shadowBlur: 18,
            shadowColor: 'rgba(8, 18, 35, 0.3)',
          },
        })),
        links: graph.edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          relation: edge.relation,
          label: {
            show: true,
            color: 'rgba(214, 227, 255, 0.72)',
            formatter: edge.relation,
          },
        })),
      },
    ],
  };

  return (
    <div className="graph-canvas">
      <ReactECharts option={option} style={{ height: 620 }} notMerge lazyUpdate />
    </div>
  );
}
