import {
  ApartmentOutlined,
  FileSearchOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Button, Form, Input, Typography, message } from 'antd';
import { motion, useReducedMotion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

import authApi from '@/api/authApi';
import { persistSession } from '@/utils/auth';

const { Paragraph, Title } = Typography;

const trustSignals = [
  {
    icon: <FileSearchOutlined />,
    title: '证据回溯',
    copy: '每次回答都围绕引用与证据片段组织，减少无出处结论。',
  },
  {
    icon: <ApartmentOutlined />,
    title: '图谱联动',
    copy: '实体、社区与邻居关系直接回流到问答与分析链路。',
  },
  {
    icon: <SafetyCertificateOutlined />,
    title: '角色授权',
    copy: '权限、文档可见性与登录鉴权保持在同一企业边界内。',
  },
];

const workflowSteps = [
  '上传制度、规范与产品资料',
  '发起面向建材业务的问题',
  '查看引用、证据与图谱关系',
  '回看任务、追踪与评估结果',
];

interface LoginFormValues {
  username: string;
  password: string;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();

  const posterMotion = shouldReduceMotion
    ? {}
    : {
        initial: { opacity: 0, x: -28 },
        animate: { opacity: 1, x: 0 },
        transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
      };

  const panelMotion = shouldReduceMotion
    ? {}
    : {
        initial: { opacity: 0, x: 24, scale: 0.98 },
        animate: { opacity: 1, x: 0, scale: 1 },
        transition: { duration: 0.46, delay: 0.08, ease: [0.22, 1, 0.36, 1] as const },
      };

  const handleSubmit = async (values: LoginFormValues) => {
    try {
      const session = await authApi.login(values);
      persistSession(session);
      message.success('登录成功');
      navigate('/qa');
    } catch {
      message.error('登录失败，请检查账号密码');
    }
  };

  return (
    <div className="login-shell">
      <motion.section className="login-poster" {...posterMotion}>
        <div className="login-grid-glow" />
        <div className="login-brand-lockup">
          <div className="login-kicker">建材知识数据中枢</div>
          <Title className="login-title">匠图智答</Title>
          <Paragraph className="login-description">
            面向企业内网的知识问答、文档治理、图谱洞察与审计闭环工作台。先确保可信，再提升检索与推理效率。
          </Paragraph>
        </div>

        <div className="login-trust-grid">
          {trustSignals.map((item, index) => (
            <motion.div
              key={item.title}
              className="trust-card"
              initial={shouldReduceMotion ? undefined : { opacity: 0, y: 16 }}
              animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
              transition={shouldReduceMotion ? undefined : { duration: 0.34, delay: 0.16 + index * 0.06 }}
            >
              <div className="trust-icon">{item.icon}</div>
              <div className="trust-title">{item.title}</div>
              <div className="trust-copy">{item.copy}</div>
            </motion.div>
          ))}
        </div>

        <div className="login-workflow">
          <div className="workflow-label">工作流</div>
          <div className="workflow-list">
            {workflowSteps.map((step, index) => (
              <div key={step} className="workflow-item">
                <div className="workflow-step">{String(index + 1).padStart(2, '0')}</div>
                <div className="workflow-copy">{step}</div>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      <motion.section className="login-panel-shell" {...panelMotion}>
        <div className="login-panel">
          <div className="surface-eyebrow">Access Portal</div>
          <Title level={2} className="login-panel-title">
            登录工作台
          </Title>
          <Paragraph className="login-panel-description">输入企业账号，进入建材知识检索与治理控制台。</Paragraph>

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
            <Button type="primary" htmlType="submit" size="large" block className="button-primary">
              进入工作台
            </Button>
          </Form>

          <div className="login-credentials">
            <div className="surface-eyebrow">测试账号</div>
            <div className="credential-row">
              <span className="credential-role">管理员</span>
              <code className="credential-value">admin / Admin@123</code>
            </div>
            <div className="credential-row">
              <span className="credential-role">采购岗</span>
              <code className="credential-value">buyer / Buyer@123</code>
            </div>
            <div className="credential-row">
              <span className="credential-role">普通员工</span>
              <code className="credential-value">staff / Staff@123</code>
            </div>
          </div>
        </div>
      </motion.section>
    </div>
  );
}
