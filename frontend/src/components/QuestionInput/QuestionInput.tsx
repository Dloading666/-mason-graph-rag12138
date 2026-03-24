import { ClearOutlined, SendOutlined } from '@ant-design/icons';
import { Button, Input, Space, Typography } from 'antd';

const { Text } = Typography;

interface QuestionInputProps {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  onClear: () => void;
}

export default function QuestionInput({
  value,
  loading,
  onChange,
  onSend,
  onClear,
}: QuestionInputProps) {
  return (
    <div className="question-composer">
      <Input.TextArea
        size="large"
        autoSize={{ minRows: 4, maxRows: 8 }}
        className="question-textarea"
        value={value}
        placeholder="请输入建材相关问题，例如：抗裂砂浆施工规范、外墙保温合规要求"
        onChange={(event) => onChange(event.target.value)}
        onPressEnter={(event) => {
          if (!event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
        disabled={loading}
      />
      <div className="question-toolbar">
        <Text className="question-hint">Enter 发送，Shift + Enter 换行</Text>
        <Space wrap>
          <Button size="large" icon={<ClearOutlined />} disabled={loading} onClick={onClear} className="secondary-button">
            清空
          </Button>
          <Button
            size="large"
            icon={<SendOutlined />}
            type="primary"
            loading={loading}
            onClick={onSend}
            className="accent-button"
          >
            发送问题
          </Button>
        </Space>
      </div>
    </div>
  );
}
