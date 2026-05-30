import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { TableRowSelection } from 'antd/es/table/interface';
import type { RequirementResponse } from '../types/models';
import { getRequirementRefId } from '../utils/requirementMapper';
import TableSelectAllBar from './TableSelectAllBar';

const priorityLabels: Record<string, string> = {
  High: '高',
  Medium: '中',
  Low: '低',
};

interface Props {
  requirements: RequirementResponse[];
  loading?: boolean;
  selectedRowKeys: React.Key[];
  onSelectionChange: (keys: React.Key[]) => void;
  emptyText?: string;
}

const columns: ColumnsType<RequirementResponse> = [
  {
    title: '需求名',
    dataIndex: 'title',
    key: 'title',
    width: 180,
    ellipsis: true,
    render: (_: unknown, record) => record.title?.trim() || record.raw_text,
  },
  {
    title: '编号',
    key: 'ref_id',
    width: 130,
    ellipsis: true,
    render: (_: unknown, record) => (
      <code style={{ fontSize: 12 }} title={record.external_id ? `内部ID: ${record.id}` : undefined}>
        {getRequirementRefId(record)}
      </code>
    ),
  },
  {
    title: '需求内容',
    dataIndex: 'raw_text',
    key: 'raw_text',
    ellipsis: true,
  },
  {
    title: '风险',
    key: 'risk',
    width: 110,
    render: (_: unknown, record) =>
      record.risk_score ? (
        <Tag color={record.priority === 'High' ? 'red' : 'blue'}>
          {priorityLabels[record.priority ?? ''] ?? record.priority} / {record.risk_score}
        </Tag>
      ) : (
        <Tag>待分析</Tag>
      ),
  },
];

export default function StructuredRequirementTable({
  requirements,
  loading,
  selectedRowKeys,
  onSelectionChange,
  emptyText = '暂无已结构化需求，请先在需求输入页完成结构化。',
}: Props) {
  const allKeys = requirements.map((r) => r.id);
  const rowSelection: TableRowSelection<RequirementResponse> = {
    selectedRowKeys,
    onChange: (keys) => onSelectionChange(keys),
    preserveSelectedRowKeys: true,
  };

  return (
    <>
      <TableSelectAllBar
        totalCount={requirements.length}
        selectedCount={selectedRowKeys.length}
        allKeys={allKeys}
        onChange={onSelectionChange}
      />
      <Table<RequirementResponse>
      rowKey="id"
      dataSource={requirements}
      columns={columns}
      rowSelection={rowSelection}
      loading={loading}
      pagination={{ pageSize: 10, showSizeChanger: false }}
      scroll={{ x: 720 }}
      locale={{ emptyText }}
    />
    </>
  );
}
