import ReactECharts from 'echarts-for-react';

import type { GraphResponse } from '@/types/graph';

interface GraphVisualProps {
  graph: GraphResponse;
}

export default function GraphVisual({ graph }: GraphVisualProps) {
  const palette = ['#64748B', '#F97316', '#0F766E', '#C98A1B', '#475569', '#1D4ED8'];
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
    animationDuration: 700,
    animationDurationUpdate: 400,
    tooltip: {
      backgroundColor: 'rgba(17, 24, 39, 0.94)',
      borderWidth: 0,
      textStyle: {
        color: '#E2E8F0',
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
          color: '#E2E8F0',
          fontSize: 11,
        },
        force: {
          repulsion: 300,
          edgeLength: [90, 170],
          gravity: 0.08,
        },
        lineStyle: {
          color: 'rgba(148, 163, 184, 0.36)',
          width: 1.4,
          curveness: 0.18,
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 6],
        emphasis: {
          focus: 'adjacency',
          label: { show: true },
          lineStyle: {
            width: 2.2,
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
            borderColor: 'rgba(248, 250, 252, 0.92)',
            borderWidth: 1.6,
            shadowBlur: 16,
            shadowColor: 'rgba(15, 23, 42, 0.32)',
          },
        })),
        links: graph.edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          relation: edge.relation,
          label: {
            show: true,
            color: 'rgba(226, 232, 240, 0.72)',
            formatter: edge.relation,
          },
        })),
      },
    ],
  };

  return (
    <div className="graph-canvas">
      <ReactECharts option={option} style={{ height: 560 }} notMerge lazyUpdate />
    </div>
  );
}
