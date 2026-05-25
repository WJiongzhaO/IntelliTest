import { useState } from 'react';
import {
  Button,
  Card,
  Input,
  message,
  Space,
  Tabs,
  Upload,
  type UploadProps,
} from 'antd';
import { DeleteOutlined, InboxOutlined, PlusOutlined } from '@ant-design/icons';
import { useRequirementStore } from '../stores/requirementStore';

const { Dragger } = Upload;
const { TextArea } = Input;

function CsvUpload() {
  const { addByCsv, loading } = useRequirementStore();

  const props: UploadProps = {
    accept: '.csv',
    maxCount: 1,
    beforeUpload: async (file) => {
      const result = await addByCsv(file);
      if (result.length > 0) {
        message.success(`已从 CSV 解析 ${result.length} 条需求`);
      }
      return false;
    },
    onRemove: () => undefined,
  };

  return (
    <Dragger {...props} disabled={loading}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">点击或拖拽 CSV 文件到此处</p>
      <p className="ant-upload-hint">
        CSV 可包含 title/name/需求名 列和 requirement/description/需求描述列。
      </p>
    </Dragger>
  );
}

function TextInput() {
  const { addByText, loading } = useRequirementStore();
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');

  const handleSubmit = async () => {
    if (!title.trim() || !text.trim()) return;
    const result = await addByText(text, title.trim());
    if (result.length > 0) {
      message.success(`已解析 ${result.length} 条需求`);
      setTitle('');
      setText('');
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="需求名（必填）"
        disabled={loading}
      />
      <TextArea
        rows={8}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={
          '在这里输入用户需求。\n\n多条需求可以用空行分隔，也可以使用编号：\n1. 第一条需求\n2. 第二条需求'
        }
        disabled={loading}
      />
      <Button
        type="primary"
        onClick={handleSubmit}
        loading={loading}
        disabled={!title.trim() || !text.trim()}
      >
        解析需求
      </Button>
    </Space>
  );
}

function ManualForm() {
  const { addByForm, loading } = useRequirementStore();
  const [entries, setEntries] = useState<{ key: number; title: string; text: string }[]>([
    { key: 0, title: '', text: '' },
  ]);

  const addRow = () => {
    setEntries([...entries, { key: Date.now(), title: '', text: '' }]);
  };

  const removeRow = (key: number) => {
    if (entries.length <= 1) return;
    setEntries(entries.filter((e) => e.key !== key));
  };

  const updateRow = (key: number, patch: Partial<{ title: string; text: string }>) => {
    setEntries(entries.map((e) => (e.key === key ? { ...e, ...patch } : e)));
  };

  const handleSubmit = async () => {
    const filled = entries.filter((e) => e.title.trim() && e.text.trim());
    if (filled.length === 0) return;
    const payload = filled.map((e) => ({
      title: e.title.trim(),
      raw_text: e.text.trim(),
    }));
    const result = await addByForm(payload);
    if (result.length > 0) {
      message.success(`已创建 ${result.length} 条需求`);
      setEntries([{ key: Date.now(), title: '', text: '' }]);
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      {entries.map((entry) => (
        <Space key={entry.key} style={{ display: 'flex', width: '100%' }} align="start">
          <Input
            style={{ width: 220 }}
            value={entry.title}
            onChange={(e) => updateRow(entry.key, { title: e.target.value })}
            placeholder="需求名（必填）"
            disabled={loading}
          />
          <Input
            style={{ flex: 1 }}
            value={entry.text}
            onChange={(e) => updateRow(entry.key, { text: e.target.value })}
            placeholder="输入单条需求描述..."
            disabled={loading}
          />
          {entries.length > 1 && (
            <Button
              icon={<DeleteOutlined />}
              danger
              onClick={() => removeRow(entry.key)}
              disabled={loading}
            />
          )}
        </Space>
      ))}
      <Space>
        <Button icon={<PlusOutlined />} onClick={addRow} disabled={loading}>
          添加一条
        </Button>
        <Button
          type="primary"
          onClick={handleSubmit}
          loading={loading}
          disabled={!entries.some((e) => e.title.trim() && e.text.trim())}
        >
          提交全部
        </Button>
      </Space>
    </Space>
  );
}

export default function RequirementInputPanel() {
  const items = [
    { key: 'text', label: '文本输入', children: <TextInput /> },
    { key: 'csv', label: 'CSV 导入', children: <CsvUpload /> },
    { key: 'form', label: '逐条录入', children: <ManualForm /> },
  ];

  return (
    <Card title="录入需求" style={{ marginBottom: 24 }}>
      <Tabs items={items} defaultActiveKey="text" />
    </Card>
  );
}
