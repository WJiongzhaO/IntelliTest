import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Col,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { TableRowSelection } from 'antd/es/table/interface';
import { DownloadOutlined } from '@ant-design/icons';
import { getRiskDashboard } from '../api/risk';
import { listRequirements } from '../api/requirements';
import TableSelectAllBar from '../components/TableSelectAllBar';
import type { RequirementResponse, RiskDashboardSummary } from '../types/models';
import { getRequirementRefId } from '../utils/requirementMapper';
import { downloadRiskRegisterCsv, requirementToRiskRegisterRow } from '../utils/riskRegisterExport';

const { Title, Text } = Typography;

const priorityLabels: Record<string, string> = {
  High: '高',
  Medium: '中',
  Low: '低',
};

function priorityColor(priority: string) {
  if (priority === 'High') return 'red';
  if (priority === 'Medium') return 'gold';
  return 'green';
}

function sortByRiskScore(a: RequirementResponse, b: RequirementResponse): number {
  return (b.risk_score ?? 0) - (a.risk_score ?? 0);
}

export default function RiskDashboardPage() {
  const [summary, setSummary] = useState<RiskDashboardSummary | null>(null);
  const [requirements, setRequirements] = useState<RequirementResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [dashboard, rows] = await Promise.all([getRiskDashboard(20), listRequirements()]);
      setSummary(dashboard);
      setRequirements(rows);
    } catch {
      message.warning('风险数据加载失败，请确认后端可用且已执行风险分析');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const analyzedRequirements = useMemo(
    () => requirements.filter((r) => r.risk_score != null).sort(sortByRiskScore),
    [requirements],
  );

  const allAnalyzedKeys = useMemo(
    () => analyzedRequirements.map((r) => r.id),
    [analyzedRequirements],
  );

  const columns: ColumnsType<RequirementResponse> = [
    {
      title: '编号',
      key: 'ref',
      width: 110,
      render: (_: unknown, record) => (
        <code style={{ fontSize: 12 }}>{getRequirementRefId(record)}</code>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title: string | null | undefined, record) =>
        title?.trim() || record.raw_text.slice(0, 80),
    },
    { title: '影响', dataIndex: 'risk_impact', width: 72 },
    { title: '概率', dataIndex: 'risk_likelihood', width: 72 },
    { title: '风险分', dataIndex: 'risk_score', width: 72 },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 100,
      render: (priority: string) => (
        <Tag color={priorityColor(priority)}>{priorityLabels[priority] ?? priority}</Tag>
      ),
    },
    {
      title: '影响理由',
      dataIndex: 'risk_impact_rationale',
      ellipsis: true,
    },
    {
      title: '概率理由',
      dataIndex: 'risk_likelihood_rationale',
      ellipsis: true,
    },
  ];

  const rowSelection: TableRowSelection<RequirementResponse> = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
    getCheckboxProps: (record) => ({
      disabled: record.risk_score == null,
    }),
  };

  const handleExport = () => {
    const selected =
      selectedRowKeys.length > 0
        ? analyzedRequirements.filter((r) => selectedRowKeys.includes(r.id))
        : [];

    if (selected.length === 0) {
      message.warning('请先勾选要导出的已分析需求');
      return;
    }

    const rows = selected
      .map(requirementToRiskRegisterRow)
      .filter((row): row is NonNullable<typeof row> => row != null);

    if (rows.length === 0) {
      message.warning('所选需求缺少完整风险字段，无法导出');
      return;
    }

    downloadRiskRegisterCsv(rows);
    message.success(`已导出 ${rows.length} 条风险登记记录（risk_register.csv）`);
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div className="section-heading">
        <div>
          <Title level={3}>风险分析面板</Title>
          <Text className="muted-text">
            展示 FR 2.0 持久化的影响、概率、风险分、优先级与理由；可导出同结构 CSV
          </Text>
        </div>
        <Space wrap>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
            disabled={analyzedRequirements.length === 0}
          >
            导出风险登记册
          </Button>
          <Button onClick={() => void loadData()} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      <Alert
        showIcon
        type="info"
        message="请先在需求输入页执行风险分析。导出列与数据库字段一致（不含模块、风险场景等未持久化字段）。导入 juice_shop_requirements.csv 时「Module」列会写入需求记录，供需求页查看，但不进入风险登记册。"
      />

      <Row gutter={[16, 16]}>
        <Col xs={12} lg={6}>
          <div className="tool-panel">
            <Statistic title="需求总数" value={summary?.total_requirements ?? 0} loading={loading} />
          </div>
        </Col>
        <Col xs={12} lg={6}>
          <div className="tool-panel">
            <Statistic title="已分析" value={summary?.analyzed_count ?? 0} loading={loading} />
          </div>
        </Col>
        <Col xs={12} lg={6}>
          <div className="tool-panel">
            <Statistic title="高风险" value={summary?.priority_high ?? 0} loading={loading} />
          </div>
        </Col>
        <Col xs={12} lg={6}>
          <div className="tool-panel">
            <Statistic
              title="平均风险分"
              precision={1}
              value={summary?.average_risk_score ?? 0}
              loading={loading}
            />
          </div>
        </Col>
      </Row>

      <div className="tool-panel">
        <TableSelectAllBar
          totalCount={analyzedRequirements.length}
          selectedCount={selectedRowKeys.length}
          allKeys={allAnalyzedKeys}
          onChange={setSelectedRowKeys}
        />
        <Table<RequirementResponse>
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={analyzedRequirements}
          rowSelection={rowSelection}
          pagination={{ pageSize: 20, showSizeChanger: true }}
          locale={{ emptyText: '暂无已分析需求，请先在需求页执行风险分析' }}
        />
      </div>
    </Space>
  );
}
