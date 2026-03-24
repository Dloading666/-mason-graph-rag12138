import {
  ApartmentOutlined,
  FileSearchOutlined,
  FileTextOutlined,
  FundOutlined,
  LogoutOutlined,
  MenuOutlined,
  ProfileOutlined,
  SettingOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import { Avatar, Button, Drawer, Grid, Layout, Menu, Space, Tag } from 'antd';
import type { MenuProps } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';

import { logout, readSession } from '@/store/session';

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;

const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  purchase: '采购岗',
  normal: '普通员工',
  guest: '访客',
};

const ROUTE_META: Record<string, { label: string; title: string; description: string }> = {
  '/qa': {
    label: 'Question Workspace',
    title: '智能问答工作台',
    description: '围绕施工规范、材料参数与采购制度提问，并返回可核验的引用与证据。',
  },
  '/documents': {
    label: 'Knowledge Ingestion',
    title: '文档治理中心',
    description: '统一管理上传、权限、增量入库与版本状态，让知识源保持可追踪。',
  },
  '/graph': {
    label: 'Graph Insight',
    title: '知识图谱关系视图',
    description: '把文档中的实体、关系与社区结构组织成可浏览的知识网络。',
  },
  '/jobs': {
    label: 'Task Center',
    title: '任务中心',
    description: '查看文档入库、研究报告与评估任务的执行状态、耗时和结果。',
  },
  '/traces': {
    label: 'Trace Center',
    title: '追踪中心',
    description: '按问题、模式与时间查看问答推理轨迹、证据链与调试信息。',
  },
  '/settings': {
    label: 'System Governance',
    title: '系统配置与评估',
    description: '查看当前部署能力，并运行基础评估闭环来比较不同检索模式。',
  },
};

const menuItems: MenuProps['items'] = [
  { key: '/qa', label: '智能问答', icon: <FileSearchOutlined /> },
  { key: '/documents', label: '文档管理', icon: <FileTextOutlined /> },
  { key: '/graph', label: '知识图谱', icon: <ApartmentOutlined /> },
  { key: '/jobs', label: '任务中心', icon: <UnorderedListOutlined /> },
  { key: '/traces', label: '追踪中心', icon: <ProfileOutlined /> },
  { key: '/settings', label: '系统设置', icon: <SettingOutlined /> },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const session = readSession();
  const screens = useBreakpoint();
  const isMobile = !screens.lg;
  const [drawerOpen, setDrawerOpen] = useState(false);
  const currentMeta = ROUTE_META[location.pathname] ?? ROUTE_META['/qa'];
  const roleLabel = ROLE_LABELS[session.user?.role ?? 'guest'] ?? session.user?.role ?? '访客';

  const handleNavigate = (key: string) => {
    navigate(key);
    setDrawerOpen(false);
  };

  const handleLogout = () => {
    logout();
    setDrawerOpen(false);
    navigate('/login');
  };

  const navigation = (
    <>
      <div className="brand-panel">
        <div className="brand-mark">JT</div>
        <div className="brand-block">
          <div className="brand-title">匠图智答</div>
          <div className="brand-subtitle">MasonGraphRAG</div>
          <p className="brand-description">建材企业知识检索、证据追溯与图谱工作台</p>
        </div>
      </div>

      <div className="nav-label">工作台</div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => handleNavigate(key)}
        className="app-menu"
      />

      <div className="sider-footnote">
        <div className="sider-footnote-label">当前重点</div>
        <div className="sider-footnote-text">
          图谱检索、任务追踪与评估闭环已经接入主流程，可继续向深度研究与更细粒度图社区演进。
        </div>
      </div>
    </>
  );

  return (
    <Layout className="app-layout">
      {!isMobile ? (
        <Sider width={280} className="app-sider">
          {navigation}
        </Sider>
      ) : (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={300}
          rootClassName="app-drawer-root"
          className="app-drawer"
          closable={false}
        >
          <div className="app-drawer-body">{navigation}</div>
        </Drawer>
      )}
      <Layout className="app-main">
        <Header className="app-header">
          <div className="topbar-shell">
            <div className="topbar-main">
              {isMobile ? (
                <Button
                  type="text"
                  icon={<MenuOutlined />}
                  className="menu-toggle"
                  onClick={() => setDrawerOpen(true)}
                />
              ) : null}
              <div>
                <div className="topbar-label">{currentMeta.label}</div>
                <div className="topbar-title">{currentMeta.title}</div>
                <div className="topbar-description">{currentMeta.description}</div>
              </div>
            </div>
            <Space size={12} wrap className="topbar-actions">
              <div className="signal-pill">
                <span className="signal-pill-label">运行状态</span>
                <strong>
                  <FundOutlined style={{ marginRight: 6 }} />
                  企业内网 / 证据优先
                </strong>
              </div>
              <div className="user-chip">
                <Avatar className="user-avatar">{session.user?.display_name?.slice(0, 1) ?? '匠'}</Avatar>
                <div className="user-copy">
                  <div className="user-name">{session.user?.display_name ?? '访客'}</div>
                  <Tag className="role-chip">{roleLabel}</Tag>
                </div>
              </div>
              <Button icon={<LogoutOutlined />} onClick={handleLogout} className="secondary-button">
                退出
              </Button>
            </Space>
          </div>
        </Header>
        <Content className="page-shell">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
