import { LogoutOutlined, MenuOutlined } from '@ant-design/icons';
import { Avatar, Button, Drawer, Grid, Layout } from 'antd';
import { AnimatePresence, LayoutGroup, motion, useReducedMotion } from 'framer-motion';
import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { APP_PAGE_META, APP_SHELL_GROUPS, DEFAULT_PAGE_META, ROLE_LABELS } from '@/config/appShell';
import { logout, readSession } from '@/store/session';

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const session = readSession();
  const screens = useBreakpoint();
  const shouldReduceMotion = useReducedMotion();
  const isMobile = !screens.lg;
  const [drawerOpen, setDrawerOpen] = useState(false);
  const currentMeta = APP_PAGE_META[location.pathname] ?? DEFAULT_PAGE_META;
  const roleLabel = ROLE_LABELS[session.user?.role ?? 'guest'] ?? session.user?.role ?? '访客';

  const routeMotion = shouldReduceMotion
    ? {}
    : {
        initial: { opacity: 0, y: 10 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: -8 },
        transition: { duration: 0.28, ease: [0.22, 1, 0.36, 1] as const },
      };

  const handleNavigate = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const handleLogout = () => {
    logout();
    setDrawerOpen(false);
    navigate('/login');
  };

  const navigation = (
    <div className="shell-nav">
      <div className="shell-brand">
        <div className="shell-brand-mark">JT</div>
        <div className="shell-brand-copy">
          <div className="shell-brand-name">匠图智答</div>
          <div className="shell-brand-subtitle">MasonGraphRAG Console</div>
          <p className="shell-brand-description">建材企业知识检索、证据回溯与图谱联动的一体化工作台。</p>
        </div>
      </div>

      <LayoutGroup id="shell-nav">
        <div className="shell-nav-groups">
          {APP_SHELL_GROUPS.map((group) => (
            <section key={group.id} className="shell-nav-group">
              <div className="shell-section-label">{group.label}</div>
              <div className="shell-section-description">{group.description}</div>
              <div className="shell-nav-list">
                {group.items.map((item) => {
                  const active = location.pathname === item.path;

                  return (
                    <button
                      key={item.path}
                      type="button"
                      className={`shell-nav-item ${active ? 'shell-nav-item-active' : ''}`}
                      onClick={() => handleNavigate(item.path)}
                    >
                      {active ? (
                        <motion.span
                          layoutId="shell-nav-active"
                          className="shell-nav-item-highlight"
                          transition={{ type: 'spring', bounce: 0.18, duration: 0.46 }}
                        />
                      ) : null}
                      <span className="shell-nav-item-icon">{item.icon}</span>
                      <span className="shell-nav-item-copy">
                        <span className="shell-nav-item-label">{item.label}</span>
                        <span className="shell-nav-item-caption">{item.shortLabel}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </LayoutGroup>

      <div className="shell-rail-footer">
        <div className="shell-footer-user">
          <Avatar className="shell-footer-avatar">{session.user?.display_name?.slice(0, 1) ?? '匠'}</Avatar>
          <div>
            <div className="shell-footer-name">{session.user?.display_name ?? '访客'}</div>
            <div className="shell-footer-role">{roleLabel}</div>
          </div>
        </div>
        <div className="shell-footer-signal">
          <span className="shell-footer-signal-label">运行边界</span>
          <strong>企业内网 / 证据优先</strong>
        </div>
      </div>
    </div>
  );

  return (
    <Layout className="app-shell">
      {!isMobile ? (
        <Sider width={304} className="shell-rail">
          {navigation}
        </Sider>
      ) : (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={320}
          rootClassName="shell-drawer-root"
          className="shell-drawer"
          closable={false}
        >
          <div className="shell-drawer-body">{navigation}</div>
        </Drawer>
      )}
      <Layout className="shell-main">
        <Header className="shell-header">
          <div className="masthead">
            <div className="masthead-main">
              {isMobile ? (
                <Button type="text" icon={<MenuOutlined />} className="menu-toggle" onClick={() => setDrawerOpen(true)} />
              ) : null}
              <AnimatePresence mode="wait">
                <motion.div key={location.pathname} className="masthead-copy" {...routeMotion}>
                  <div className="masthead-kicker">{currentMeta.shortLabel}</div>
                  <div className="masthead-title">{currentMeta.title}</div>
                  <div className="masthead-description">{currentMeta.description}</div>
                </motion.div>
              </AnimatePresence>
            </div>

            <div className="masthead-actions">
              <div className="signal-badge">
                <span className="signal-badge-label">运行边界</span>
                <strong>内网会话 / 证据优先</strong>
              </div>
              <div className="profile-badge">
                <Avatar className="profile-badge-avatar">{session.user?.display_name?.slice(0, 1) ?? '匠'}</Avatar>
                <div className="profile-badge-copy">
                  <div className="profile-badge-name">{session.user?.display_name ?? '访客'}</div>
                  <div className="profile-badge-role">{roleLabel}</div>
                </div>
              </div>
              <Button icon={<LogoutOutlined />} onClick={handleLogout} className="button-secondary">
                退出登录
              </Button>
            </div>
          </div>
        </Header>

        <Content className="shell-content">
          <AnimatePresence mode="wait">
            <motion.div key={location.pathname} className="route-stage" {...routeMotion}>
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </Content>
      </Layout>
    </Layout>
  );
}
