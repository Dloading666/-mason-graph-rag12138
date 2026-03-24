import {
  ApartmentOutlined,
  FileSearchOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Button, Form, Input, Space, Tag, Typography, message } from 'antd';
import { useNavigate } from 'react-router-dom';

import authApi from '@/api/authApi';
import { persistSession } from '@/utils/auth';

const { Title, Paragraph, Text } = Typography;

const accessSignals = [
  {
    icon: <FileSearchOutlined className="signal-card-accent" />,
    title: '证据返回',
    copy: '每次回答都围绕引用与片段组织，减少无出处结论。',
  },
  {
    icon: <ApartmentOutlined className="signal-card-accent" />,
    title: '知识图谱',
    copy: '实体关系统一进入可视化工作面，辅助理解上下游语义。',
  },
  {
    icon: <SafetyCertificateOutlined className="signal-card-accent" />,
    title: '权限内控',
    copy: '角色、文档可见性和登录鉴权在同一企业边界内完成。',
  },
];

interface LoginFormValues {
  username: string;
  password: string;
}

export default function LoginPage() {
  const navigate = useNavigate();

  const handleSubmit = async (values: LoginFormValues) => {
    try {
      const session = await authApi.login(values);
      persistSession(session);
      message.success('登录成功');
      navigate('/qa');
    } catch (error) {
      message.error('登录失败，请检查账号密码');
    }
  };

  return (
    <div className="login-shell">
      <section className="login-intro">
        <div className="page-kicker">Private Enterprise Knowledge Console</div>
        <Title className="login-title">匠图智答</Title>
        <Paragraph className="login-description">
          建材企业私有化知识问答、文档治理与图谱洞察统一工作台。界面围绕可追溯、可授权、可复核来设计，而不是做成普通聊天框。
        </Paragraph>
        <Space wrap className="chip-cluster">
          <Tag className="utility-chip">Qwen3.5-plus</Tag>
          <Tag className="utility-chip">GraphRAG Core</Tag>
          <Tag className="utility-chip">企业内网部署</Tag>
        </Space>

        <div className="login-signal-grid">
          {accessSignals.map((item) => (
            <div key={item.title} className="signal-card">
              {item.icon}
              <div className="signal-card-title">{item.title}</div>
              <div className="signal-card-copy">{item.copy}</div>
            </div>
          ))}
        </div>

        <div className="login-note">
          <div className="login-note-label">访问原则</div>
          <p>答案必须可追溯，文档必须可授权，图谱必须可解释。先保证可信，再追求炫技。</p>
        </div>
      </section>

      <section className="login-form-shell">
        <div className="login-form-panel">
          <div>
            <div className="section-eyebrow">Access Portal</div>
            <Title level={2} className="login-form-title">
              登录系统
            </Title>
            <Paragraph className="login-form-description">输入你的企业账号，进入建材知识工作台。</Paragraph>
          </div>

          <Form
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ username: 'admin', password: 'Admin@123' }}
            className="login-form"
          >
            <Form.Item label="用户名" name="username" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input prefix={<UserOutlined />} size="large" placeholder="请输入用户名" />
            </Form.Item>
            <Form.Item label="密码" name="password" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password prefix={<LockOutlined />} size="large" placeholder="请输入密码" />
            </Form.Item>
            <Button type="primary" htmlType="submit" size="large" block className="accent-button">
              进入工作台
            </Button>
          </Form>

          <div className="login-credentials">
            <Text className="login-credential-label">默认测试账号</Text>
            <div className="chip-cluster login-credential-list">
              <Tag className="utility-chip">admin / Admin@123</Tag>
              <Tag className="utility-chip">buyer / Buyer@123</Tag>
              <Tag className="utility-chip">staff / Staff@123</Tag>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
