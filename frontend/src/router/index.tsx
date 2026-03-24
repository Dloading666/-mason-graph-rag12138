import { Suspense } from 'react';
import { Spin } from 'antd';
import { Navigate, createBrowserRouter } from 'react-router-dom';

import AppLayout from '@/components/Layout/AppLayout';
import { lazyWithRetry } from '@/router/lazyWithRetry';
import type { UserRole } from '@/types/user';
import { getCurrentUser, isAuthenticated } from '@/utils/auth';

const DocumentPage = lazyWithRetry(() => import('@/pages/Document/Document'));
const GraphPage = lazyWithRetry(() => import('@/pages/Graph/Graph'));
const JobsPage = lazyWithRetry(() => import('@/pages/Jobs/Jobs'));
const LoginPage = lazyWithRetry(() => import('@/pages/Login/Login'));
const QaPage = lazyWithRetry(() => import('@/pages/Qa/Qa'));
const SettingPage = lazyWithRetry(() => import('@/pages/Setting/Setting'));
const TracesPage = lazyWithRetry(() => import('@/pages/Traces/Traces'));

function RouteLoading() {
  return (
    <div style={{ minHeight: '50vh', display: 'grid', placeItems: 'center' }}>
      <Spin size="large" tip="页面加载中..." />
    </div>
  );
}

function withSuspense(element: JSX.Element) {
  return <Suspense fallback={<RouteLoading />}>{element}</Suspense>;
}

function RequireAuth({ children, allowedRoles }: { children: JSX.Element; allowedRoles?: UserRole[] }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  const user = getCurrentUser();
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/qa" replace />;
  }

  return children;
}

const router = createBrowserRouter([
  {
    path: '/login',
    element: withSuspense(<LoginPage />),
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to="/qa" replace /> },
      { path: '/qa', element: withSuspense(<QaPage />) },
      { path: '/documents', element: withSuspense(<DocumentPage />) },
      { path: '/graph', element: withSuspense(<GraphPage />) },
      { path: '/jobs', element: withSuspense(<JobsPage />) },
      { path: '/traces', element: withSuspense(<TracesPage />) },
      {
        path: '/settings',
        element: (
          <RequireAuth allowedRoles={['admin']}>
            {withSuspense(<SettingPage />)}
          </RequireAuth>
        ),
      },
    ],
  },
]);

export default router;
