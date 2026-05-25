import { useEffect, useState } from 'react';
import { Alert, Col, Row, Space, Statistic, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { getRiskDashboard } from '../api/risk';
import type { RiskAssessment, RiskDashboardSummary } from '../types/models';

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

export default function RiskDashboardPage() {
  const [summary, setSummary] = useState<RiskDashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    void getRiskDashboard()
      .then(setSummary)
      .catch(() => message.warning('风险统计暂时不可用，请先在需求页执行风险分析'))
      .finally(() => setLoading(false));
  }, []);

  const columns: ColumnsType<RiskAssessment> = [
    {
      title: '需求',
      dataIndex: 'requirement_title',
      render: (_: unknown, record) => record.requirement_title || record.requirement_id,
    },
    { title: '影响', dataIndex: 'impact', width: 80 },
    { title: '概率', dataIndex: 'likelihood', width: 80 },
    { title: '分数', dataIndex: 'risk_score', width: 80 },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 120,
      render: (priority: string) => (
        <Tag color={priorityColor(priority)}>{priorityLabels[priority] ?? priority}</Tag>
      ),
    },
    { title: '理由', dataIndex: 'impact_rationale', ellipsis: true },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div className="section-heading">
        <div>
          <Title level={3}>风险分析面板</Title>
          <Text className="muted-text">按风险分数查看需求优先级</Text>
        </div>
      </div>

      <Alert
        showIcon
        type="info"
        message="请先在需求输入页对已结构化需求执行风险分析，随后这里会展示统计结果。"
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
        <Table<RiskAssessment>
          rowKey="requirement_id"
          loading={loading}
          columns={columns}
          dataSource={summary?.highest_risk ?? []}
          pagination={false}
        />
      </div>
    </Space>
  );
}
