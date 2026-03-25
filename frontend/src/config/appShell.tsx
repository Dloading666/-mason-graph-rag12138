import {
  ApartmentOutlined,
  FileSearchOutlined,
  FileTextOutlined,
  ProfileOutlined,
  SettingOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import type { ReactNode } from 'react';

export type AppShellGroupId = 'knowledge' | 'governance';

export interface AppShellItem {
  path: string;
  group: AppShellGroupId;
  label: string;
  shortLabel: string;
  title: string;
  description: string;
  icon: ReactNode;
}

export interface AppShellGroup {
  id: AppShellGroupId;
  label: string;
  description: string;
  items: AppShellItem[];
}

export const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  purchase: '采购岗',
  normal: '普通员工',
  guest: '访客',
};

const shellItems: AppShellItem[] = [
  {
    path: '/qa',
    group: 'knowledge',
    label: '智能问答',
    shortLabel: '问答工作台',
    title: '智能问答工作台',
    description: '围绕规范、制度、参数与证据链发起提问，查看可核验的答案与追踪信息。',
    icon: <FileSearchOutlined />,
  },
  {
    path: '/documents',
    group: 'knowledge',
    label: '文档治理',
    shortLabel: '知识入库',
    title: '文档治理中心',
    description: '统一管理上传、授权、增量入库与版本状态，维持知识源的清晰边界。',
    icon: <FileTextOutlined />,
  },
  {
    path: '/graph',
    group: 'knowledge',
    label: '知识图谱',
    shortLabel: '关系网络',
    title: '知识图谱视图',
    description: '查看实体、关系与社区结构，辅助解释问答链路与知识覆盖范围。',
    icon: <ApartmentOutlined />,
  },
  {
    path: '/jobs',
    group: 'governance',
    label: '任务中心',
    shortLabel: '异步队列',
    title: '任务中心',
    description: '跟踪文档入库、研究报告与评估任务的执行进度、结果与异常。',
    icon: <UnorderedListOutlined />,
  },
  {
    path: '/traces',
    group: 'governance',
    label: '追踪审计',
    shortLabel: '推理轨迹',
    title: '追踪审计中心',
    description: '按问题、模式与时间回看答案、引用、计划、调试信息与证据链。',
    icon: <ProfileOutlined />,
  },
  {
    path: '/settings',
    group: 'governance',
    label: '系统治理',
    shortLabel: '评估与配置',
    title: '系统治理与评估',
    description: '查看部署能力、权限边界与评估结果，维持平台可用性与可审计性。',
    icon: <SettingOutlined />,
  },
];

export const APP_SHELL_GROUPS: AppShellGroup[] = [
  {
    id: 'knowledge',
    label: '问答与知识',
    description: '面向一线使用者的检索、入库与图谱联动。',
    items: shellItems.filter((item) => item.group === 'knowledge'),
  },
  {
    id: 'governance',
    label: '运行与治理',
    description: '面向管理员与审计者的任务、追踪与评估闭环。',
    items: shellItems.filter((item) => item.group === 'governance'),
  },
];

export const APP_PAGE_META = Object.fromEntries(shellItems.map((item) => [item.path, item])) as Record<
  string,
  AppShellItem
>;

export const DEFAULT_PAGE_META = APP_PAGE_META['/qa'];
