import React from 'react';
import ReactDOM from 'react-dom/client';
import { App as AntdApp, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

import App from '@/App';
import '@/styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#56677b',
          colorInfo: '#56677b',
          colorSuccess: '#2f855a',
          colorWarning: '#d97706',
          colorError: '#c05621',
          colorTextBase: '#21303d',
          colorBgBase: '#f3f5f7',
          colorBorder: '#d4dde4',
          borderRadius: 16,
          borderRadiusLG: 24,
          borderRadiusSM: 12,
          boxShadowSecondary: '0 24px 50px rgba(27, 40, 53, 0.14)',
          fontFamily: '"Bahnschrift", "Aptos", "PingFang SC", "Microsoft YaHei UI", sans-serif',
        },
      }}
    >
      <AntdApp>
        <App />
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>,
);
