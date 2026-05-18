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
import { InboxOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
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
        message.success(`Parsed ${result.length} requirements from CSV`);
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
      <p className="ant-upload-text">Click or drag a CSV file here</p>
      <p className="ant-upload-hint">
        The file should have a column containing requirement descriptions
      </p>
    </Dragger>
  );
}

function TextInput() {
  const { addByText, loading } = useRequirementStore();
  const [text, setText] = useState('');

  const handleSubmit = async () => {
    if (!text.trim()) return;
    const result = await addByText(text);
    if (result.length > 0) {
      message.success(`Parsed ${result.length} requirements`);
      setText('');
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <TextArea
        rows={8}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={
          'Paste requirement text here.\n\nSeparate multiple requirements with blank lines, or use numbered items:\n1. First requirement\n2. Second requirement'
        }
        disabled={loading}
      />
      <Button type="primary" onClick={handleSubmit} loading={loading} disabled={!text.trim()}>
        Parse Requirements
      </Button>
    </Space>
  );
}

function ManualForm() {
  const { addByForm, loading } = useRequirementStore();
  const [entries, setEntries] = useState<{ key: number; text: string }[]>([
    { key: 0, text: '' },
  ]);

  const addRow = () => {
    setEntries([...entries, { key: Date.now(), text: '' }]);
  };

  const removeRow = (key: number) => {
    if (entries.length <= 1) return;
    setEntries(entries.filter((e) => e.key !== key));
  };

  const updateRow = (key: number, value: string) => {
    setEntries(entries.map((e) => (e.key === key ? { ...e, text: value } : e)));
  };

  const handleSubmit = async () => {
    const filled = entries.filter((e) => e.text.trim());
    if (filled.length === 0) return;
    const payload = filled.map((e) => ({ raw_text: e.text.trim() }));
    const result = await addByForm(payload);
    if (result.length > 0) {
      message.success(`Created ${result.length} requirements`);
      setEntries([{ key: Date.now(), text: '' }]);
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      {entries.map((entry) => (
        <Space key={entry.key} style={{ display: 'flex', width: '100%' }} align="start">
          <Input
            style={{ flex: 1 }}
            value={entry.text}
            onChange={(e) => updateRow(entry.key, e.target.value)}
            placeholder="Enter a single requirement description..."
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
          Add Requirement
        </Button>
        <Button
          type="primary"
          onClick={handleSubmit}
          loading={loading}
          disabled={!entries.some((e) => e.text.trim())}
        >
          Submit All
        </Button>
      </Space>
    </Space>
  );
}

export default function RequirementInputPanel() {
  const items = [
    { key: 'csv', label: 'CSV Upload', children: <CsvUpload /> },
    { key: 'text', label: 'Text Input', children: <TextInput /> },
    { key: 'form', label: 'Manual Entry', children: <ManualForm /> },
  ];

  return (
    <Card title="Import Requirements" style={{ marginBottom: 24 }}>
      <Tabs items={items} />
    </Card>
  );
}
