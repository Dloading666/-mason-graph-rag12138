import { ClearOutlined, SendOutlined } from '@ant-design/icons';
import { Button, Input } from 'antd';

interface QuestionInputProps {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  onClear: () => void;
}

export default function QuestionInput({ value, loading, onChange, onSend, onClear }: QuestionInputProps) {
  return (
    <div className="question-composer">
      <Input.TextArea
        size="large"
        autoSize={{ minRows: 5, maxRows: 9 }}
        className="composer-textarea"
        value={value}
        placeholder="例如：抗裂砂浆施工规范有哪些关键要求？"
        onChange={(event) => onChange(event.target.value)}
        onPressEnter={(event) => {
          if (!event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
        disabled={loading}
      />
      <div className="composer-footer">
        <div className="composer-hint">Enter 发送，Shift + Enter 换行</div>
        <div className="composer-actions">
          <Button size="large" icon={<ClearOutlined />} disabled={loading} onClick={onClear} className="button-secondary">
            清空
          </Button>
          <Button
            size="large"
            icon={<SendOutlined />}
            type="primary"
            loading={loading}
            onClick={onSend}
            className="button-primary"
          >
            发送问题
          </Button>
        </div>
      </div>
    </div>
  );
}
