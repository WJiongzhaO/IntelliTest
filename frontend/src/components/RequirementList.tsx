import { useEffect } from 'react';
import { Button, Card, Descriptions, Popconfirm, Space, Table, Tag, message } from 'antd';
import {
  ThunderboltOutlined,
  DeleteOutlined,
  ReloadOutlined,
  RadarChartOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useRequirementStore } from '../stores/requirementStore';
import type { RequirementResponse } from '../types';
import { getRequirementDisplayName } from '../utils/requirementMapper';

const sourceLabels: Record<string, string> = {
  csv: 'CSV',
  text: '文本',
  form: '表单',
};

const sourceColors: Record<string, string> = {
  csv: 'blue',
  text: 'green',
  form: 'orange',
};

const priorityLabels: Record<string, string> = {
  High: '高',
  Medium: '中',
  Low: '低',
};

interface Props {
  onStructure: (id: string) => Promise<void>;
  onRisk: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  loading: boolean;
}

function buildColumns({
  onStructure,
  onRisk,
  onDelete,
  loading,
}: Props): ColumnsType<RequirementResponse> {
  return [
    {
      title: '需求名',
      dataIndex: 'title',
      key: 'title',
      width: 180,
      ellipsis: true,
      render: (_: unknown, record: RequirementResponse) => getRequirementDisplayName(record),
    },
    {
      title: '编号',
      dataIndex: 'id',
      key: 'id',
      width: 120,
      ellipsis: true,
      render: (id: string) => <code style={{ fontSize: 12 }}>{id}</code>,
    },
    {
      title: '需求内容',
      dataIndex: 'raw_text',
      key: 'raw_text',
      ellipsis: true,
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 90,
      render: (t: string) => (
        <Tag color={sourceColors[t] || 'default'}>{sourceLabels[t] ?? t}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_structured',
      key: 'is_structured',
      width: 110,
      render: (v: boolean) =>
        v ? <Tag color="success">已结构化</Tag> : <Tag color="default">原始</Tag>,
    },
    {
      title: '风险',
      dataIndex: 'priority',
      key: 'priority',
      width: 110,
      render: (_: unknown, record: RequirementResponse) =>
        record.risk_score ? (
          <Tag color={record.priority === 'High' ? 'red' : 'blue'}>
            {priorityLabels[record.priority ?? ''] ?? record.priority} / {record.risk_score}
          </Tag>
        ) : (
          <Tag>待分析</Tag>
        ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 280,
      render: (_: unknown, record: RequirementResponse) => (
        <Space>
          {!record.is_structured && (
            <Popconfirm
              title="确认调用大模型进行结构化？"
              onConfirm={() => onStructure(record.id)}
              okText="确认"
              cancelText="取消"
            >
              <Button size="small" icon={<ThunderboltOutlined />} loading={loading}>
                结构化
              </Button>
            </Popconfirm>
          )}
          {record.is_structured && (
            <Button
              size="small"
              icon={<RadarChartOutlined />}
              loading={loading}
              onClick={() => onRisk(record.id)}
            >
              风险分析
            </Button>
          )}
          <Popconfirm
            title="确认删除这条需求？"
            onConfirm={() => onDelete(record.id)}
            okText="删除"
            cancelText="取消"
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
      <Descriptions.Item label="输入字段">
        {record.input_fields.length > 0 ? record.input_fields.join(', ') : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="数据范围">
        {record.data_ranges.length > 0
          ? record.data_ranges.map((r, i) => <div key={i}>{r}</div>)
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="条件">
        {record.conditions.length > 0
          ? record.conditions.map((c, i) => <div key={i}>• {c}</div>)
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="预期动作">
        {record.expected_actions.length > 0
          ? record.expected_actions.map((a, i) => <div key={i}>• {a}</div>)
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="风险">
        {record.risk_score
          ? `${priorityLabels[record.priority ?? ''] ?? record.priority} / ${record.risk_score}（影响=${record.risk_impact}，概率=${record.risk_likelihood}）`
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="风险理由">
        {record.risk_impact_rationale || record.risk_likelihood_rationale || '-'}
      </Descriptions.Item>
    </Descriptions>
  );
}

export default function RequirementList() {
  const { requirements, loading, fetchAll, structureOne, analyzeRisk, remove } =
    useRequirementStore();

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleStructure = async (id: string) => {
    const result = await structureOne(id);
    if (result) message.success('需求结构化完成');
  };

  const handleDelete = async (id: string) => {
    await remove(id);
    message.success('需求已删除');
  };

  const handleRisk = async (id: string) => {
    await analyzeRisk(id);
    message.success('风险分析已更新');
  };

  const columns = buildColumns({
    onStructure: handleStructure,
    onRisk: handleRisk,
    onDelete: handleDelete,
    loading,
  });

  return (
    <Card
      title={`需求列表（${requirements.length}）`}
      extra={
        <Button icon={<ReloadOutlined />} onClick={fetchAll} loading={loading}>
          刷新
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
        locale={{ emptyText: '暂无需求，请先在上方录入。' }}
      />
    </Card>
  );
}
