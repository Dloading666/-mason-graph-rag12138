import React from 'react';
import ReactDOM from 'react-dom/client';
import { App as AntdApp, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

import App from '@/App';
import '@/styles/index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#3b82f6',
          colorInfo: '#3b82f6',
          colorSuccess: '#2f8f6b',
          colorWarning: '#38bdf8',
          colorError: '#cf5a58',
          colorTextBase: '#0f2138',
          colorBgBase: '#eef4fb',
          colorBorder: '#c9d8ec',
          borderRadius: 18,
          borderRadiusLG: 28,
          borderRadiusSM: 14,
          boxShadowSecondary: '0 24px 60px rgba(10, 26, 48, 0.16)',
          fontFamily: '"Aptos", "Bahnschrift", "PingFang SC", "Microsoft YaHei UI", sans-serif',
        },
        components: {
          Button: {
            controlHeight: 44,
            fontWeight: 600,
          },
          Input: {
            controlHeight: 48,
          },
          Select: {
            controlHeight: 48,
          },
          Table: {
            headerBg: 'rgba(29, 78, 216, 0.04)',
            rowHoverBg: 'rgba(59, 130, 246, 0.06)',
          },
          Tag: {
            borderRadiusSM: 999,
          },
        },
      }}
    >
      <AntdApp>
        <App />
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>,
);
