import { useEffect, useMemo, useState } from 'react';
import { Button, Card, Descriptions, Popconfirm, Space, Table, Tag, message } from 'antd';
import {
  ThunderboltOutlined,
  DeleteOutlined,
  ReloadOutlined,
  RadarChartOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { TableRowSelection } from 'antd/es/table/interface';
import { useRequirementStore } from '../stores/requirementStore';
import { useRequirementJobStore } from '../stores/requirementJobStore';
import type { RequirementResponse } from '../types';
import { getRequirementDisplayName, getRequirementRefId } from '../utils/requirementMapper';
import TableSelectAllBar from './TableSelectAllBar';

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

interface ColumnProps {
  onStructure: (record: RequirementResponse) => void;
  onRisk: (record: RequirementResponse) => void;
  onDelete: (id: string) => Promise<void>;
  isRowBusy: (id: string) => boolean;
}

function buildColumns({
  onStructure,
  onRisk,
  onDelete,
  isRowBusy,
}: ColumnProps): ColumnsType<RequirementResponse> {
  return [
    {
      title: '需求名',
      dataIndex: 'title',
      key: 'title',
      width: 180,
      ellipsis: true,
      render: (_: unknown, record: RequirementResponse) =>
        record.title?.trim() || record.raw_text,
    },
    {
      title: '编号',
      key: 'ref_id',
      width: 120,
      ellipsis: true,
      render: (_: unknown, record: RequirementResponse) => (
        <code style={{ fontSize: 12 }} title={record.external_id ? `内部ID: ${record.id}` : undefined}>
          {getRequirementRefId(record)}
        </code>
      ),
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 130,
      ellipsis: true,
      render: (module: string | null | undefined) => module?.trim() || '—',
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
      render: (_: unknown, record: RequirementResponse) => {
        const busy = isRowBusy(record.id);
        return (
          <Space>
            {!record.is_structured && (
              <Popconfirm
                title="确认调用大模型进行结构化？"
                onConfirm={() => onStructure(record)}
                okText="确认"
                cancelText="取消"
              >
                <Button size="small" icon={<ThunderboltOutlined />} loading={busy}>
                  结构化
                </Button>
              </Popconfirm>
            )}
            {record.is_structured && (
              <Button
                size="small"
                icon={<RadarChartOutlined />}
                loading={busy}
                onClick={() => onRisk(record)}
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
              <Button size="small" danger icon={<DeleteOutlined />} disabled={busy} />
            </Popconfirm>
          </Space>
        );
      },
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

function toJobItem(record: RequirementResponse) {
  return { id: record.id, title: getRequirementDisplayName(record) };
}

export default function RequirementList() {
  const { requirements, loading, fetchAll, remove, batchRemove } = useRequirementStore();
  const { enqueueStructure, enqueueRisk, isRequirementBusy } = useRequirementJobStore();
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const selectedRecords = useMemo(
    () => requirements.filter((r) => selectedRowKeys.includes(r.id)),
    [requirements, selectedRowKeys],
  );

  const batchStructureCount = selectedRecords.filter((r) => !r.is_structured).length;
  const batchRiskCount = selectedRecords.filter((r) => r.is_structured).length;

  const handleStructure = (record: RequirementResponse) => {
    enqueueStructure([toJobItem(record)]);
    message.info('已加入结构化队列');
  };

  const handleRisk = (record: RequirementResponse) => {
    enqueueRisk([toJobItem(record)]);
    message.info('已加入风险分析队列');
  };

  const handleBatchStructure = () => {
    const items = selectedRecords.filter((r) => !r.is_structured).map(toJobItem);
    if (items.length === 0) return;
    enqueueStructure(items);
    message.success(`已将 ${items.length} 条需求加入结构化队列`);
  };

  const handleBatchRisk = () => {
    const items = selectedRecords.filter((r) => r.is_structured).map(toJobItem);
    if (items.length === 0) return;
    enqueueRisk(items);
    message.success(`已将 ${items.length} 条需求加入风险分析队列`);
  };

  const handleDelete = async (id: string) => {
    await remove(id);
    setSelectedRowKeys((keys) => keys.filter((key) => key !== id));
    message.success('需求已删除');
  };

  const handleBatchDelete = async () => {
    const ids = selectedRecords.map((r) => r.id);
    await batchRemove(ids);
    setSelectedRowKeys([]);
    message.success(`已删除 ${ids.length} 条需求及其关联用例`);
  };

  const rowSelection: TableRowSelection<RequirementResponse> = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
    preserveSelectedRowKeys: true,
  };

  const columns = buildColumns({
    onStructure: handleStructure,
    onRisk: handleRisk,
    onDelete: handleDelete,
    isRowBusy: (id) => isRequirementBusy(id),
  });

  return (
    <Card
      title={`需求列表（${requirements.length}）`}
      extra={
        <Space wrap>
          {selectedRowKeys.length > 0 && (
            <>
              <Popconfirm
                title={`对选中的 ${batchStructureCount} 条未结构化需求批量结构化？`}
                onConfirm={handleBatchStructure}
                okText="确认"
                cancelText="取消"
                disabled={batchStructureCount === 0}
              >
                <Button
                  icon={<ThunderboltOutlined />}
                  disabled={batchStructureCount === 0}
                >
                  批量结构化{batchStructureCount > 0 ? ` (${batchStructureCount})` : ''}
                </Button>
              </Popconfirm>
              <Popconfirm
                title={`对选中的 ${batchRiskCount} 条已结构化需求批量风险分析？`}
                onConfirm={handleBatchRisk}
                okText="确认"
                cancelText="取消"
                disabled={batchRiskCount === 0}
              >
                <Button
                  icon={<RadarChartOutlined />}
                  disabled={batchRiskCount === 0}
                >
                  批量风险分析{batchRiskCount > 0 ? ` (${batchRiskCount})` : ''}
                </Button>
              </Popconfirm>
              <Popconfirm
                title={`确认删除选中的 ${selectedRecords.length} 条需求？关联测试用例将一并删除。`}
                onConfirm={() => void handleBatchDelete()}
                okText="删除"
                cancelText="取消"
              >
                <Button danger icon={<DeleteOutlined />}>
                  批量删除 ({selectedRecords.length})
                </Button>
              </Popconfirm>
            </>
          )}
          <Button icon={<ReloadOutlined />} onClick={fetchAll} loading={loading}>
            刷新
          </Button>
        </Space>
      }
    >
      <TableSelectAllBar
        totalCount={requirements.length}
        selectedCount={selectedRowKeys.length}
        allKeys={requirements.map((r) => r.id)}
        onChange={setSelectedRowKeys}
      />
      <Table<RequirementResponse>
        dataSource={requirements}
        columns={columns}
        rowKey="id"
        rowSelection={rowSelection}
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
