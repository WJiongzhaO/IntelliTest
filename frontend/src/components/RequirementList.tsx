import { useEffect } from 'react';
import { Button, Card, Descriptions, Popconfirm, Space, Table, Tag, message } from 'antd';
import { ThunderboltOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useRequirementStore } from '../stores/requirementStore';
import type { RequirementResponse } from '../types';

const sourceColors: Record<string, string> = {
  csv: 'blue',
  text: 'green',
  form: 'orange',
};

interface Props {
  onStructure: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  loading: boolean;
}

function buildColumns({
  onStructure,
  onDelete,
  loading,
}: Props): ColumnsType<RequirementResponse> {
  return [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 120,
      ellipsis: true,
      render: (id: string) => <code style={{ fontSize: 12 }}>{id}</code>,
    },
    {
      title: 'Requirement',
      dataIndex: 'raw_text',
      key: 'raw_text',
      ellipsis: true,
    },
    {
      title: 'Source',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 90,
      render: (t: string) => <Tag color={sourceColors[t] || 'default'}>{t.toUpperCase()}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'is_structured',
      key: 'is_structured',
      width: 110,
      render: (v: boolean) =>
        v ? <Tag color="success">Structured</Tag> : <Tag color="default">Raw</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_: unknown, record: RequirementResponse) => (
        <Space>
          {!record.is_structured && (
            <Popconfirm
              title="Send to LLM for structuring?"
              onConfirm={() => onStructure(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Button
                size="small"
                icon={<ThunderboltOutlined />}
                loading={loading}
              >
                Structure
              </Button>
            </Popconfirm>
          )}
          <Popconfirm
            title="Delete this requirement?"
            onConfirm={() => onDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button size="small" danger icon={<DeleteOutlined />} loading={loading} />
          </Popconfirm>
        </Space>
      ),
    },
  ];
}

function expandedRowRender(record: RequirementResponse) {
  if (!record.is_structured) return null;
  return (
    <Descriptions bordered size="small" column={2} style={{ marginLeft: 32 }}>
      <Descriptions.Item label="Input Fields">
        {record.input_fields.length > 0 ? record.input_fields.join(', ') : '—'}
      </Descriptions.Item>
      <Descriptions.Item label="Data Ranges">
        {record.data_ranges.length > 0
          ? record.data_ranges.map((r, i) => <div key={i}>{r}</div>)
          : '—'}
      </Descriptions.Item>
      <Descriptions.Item label="Conditions">
        {record.conditions.length > 0
          ? record.conditions.map((c, i) => <div key={i}>• {c}</div>)
          : '—'}
      </Descriptions.Item>
      <Descriptions.Item label="Expected Actions">
        {record.expected_actions.length > 0
          ? record.expected_actions.map((a, i) => <div key={i}>• {a}</div>)
          : '—'}
      </Descriptions.Item>
    </Descriptions>
  );
}

export default function RequirementList() {
  const { requirements, loading, fetchAll, structureOne, remove } = useRequirementStore();

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleStructure = async (id: string) => {
    const result = await structureOne(id);
    if (result) message.success('Requirement structured successfully');
  };

  const handleDelete = async (id: string) => {
    await remove(id);
    message.success('Requirement deleted');
  };

  const columns = buildColumns({ onStructure: handleStructure, onDelete: handleDelete, loading });

  return (
    <Card
      title={`Requirements (${requirements.length})`}
      extra={
        <Button icon={<ReloadOutlined />} onClick={fetchAll} loading={loading}>
          Refresh
        </Button>
      }
    >
      <Table<RequirementResponse>
        dataSource={requirements}
        columns={columns}
        rowKey="id"
        loading={loading}
        expandable={{
          expandedRowRender,
          rowExpandable: (r) => r.is_structured,
        }}
        scroll={{ x: 800 }}
        pagination={{ pageSize: 15, showSizeChanger: false }}
        locale={{ emptyText: 'No requirements yet. Import some above.' }}
      />
    </Card>
  );
}
