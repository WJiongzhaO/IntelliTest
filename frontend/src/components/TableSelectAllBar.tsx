import { Button, Space, Typography } from 'antd';

const { Text } = Typography;

interface Props {
  totalCount: number;
  selectedCount: number;
  allKeys: React.Key[];
  onChange: (keys: React.Key[]) => void;
}

/** Toolbar to select all rows across paginated table pages (not just current page). */
export default function TableSelectAllBar({
  totalCount,
  selectedCount,
  allKeys,
  onChange,
}: Props) {
  if (totalCount === 0) return null;

  const allSelected = selectedCount > 0 && selectedCount === totalCount;

  return (
    <Space style={{ marginBottom: 8 }} wrap>
      <Button
        size="small"
        type={allSelected ? 'default' : 'primary'}
        ghost={!allSelected}
        onClick={() => onChange(allKeys)}
        disabled={allSelected}
      >
        全选全部 ({totalCount})
      </Button>
      <Button size="small" onClick={() => onChange([])} disabled={selectedCount === 0}>
        取消全选
      </Button>
      {selectedCount > 0 && (
        <Text type="secondary">
          已选 {selectedCount} / {totalCount}
          {selectedCount < totalCount && '（表头勾选仅当前页）'}
        </Text>
      )}
    </Space>
  );
}
