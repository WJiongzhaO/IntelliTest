import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Empty,
  Popconfirm,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { listRequirements } from '../api/requirements';
import StructuredRequirementTable from '../components/StructuredRequirementTable';
import { useTestDesignJobStore } from '../stores/testDesignJobStore';
import type {
  BlackBoxTechnique,
  CoverageItem,
  RequirementResponse,
  TestCase,
  TestSuite,
} from '../types/models';
import { mergeBlackboxResults } from '../utils/blackboxResultMerge';
import { saveSuiteForReviewExport } from '../utils/exportSuiteStorage';
import { getRequirementDisplayName, toStructuredRequirement } from '../utils/requirementMapper';

const { Title, Text } = Typography;

const techniqueOptions = [
  { label: '等价类划分（EP）', value: 'EP' },
  { label: '边界值分析（BVA）', value: 'BVA' },
  { label: '判定表（DT）', value: 'DT' },
];

function buildSuite(requirementIds: string[], result: ReturnType<typeof mergeBlackboxResults>): TestSuite {
  return {
    id: `blackbox-${Date.now()}`,
    name: requirementIds.length > 1 ? '黑盒测试套件（批量）' : '黑盒测试套件',
    description: `由黑盒测试工作台生成（${requirementIds.length} 条需求）`,
    test_cases: result?.test_cases ?? [],
    created_at: new Date().toISOString(),
  };
}

export default function BlackboxWorkbench() {
  const [requirements, setRequirements] = useState<RequirementResponse[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [techniques, setTechniques] = useState<BlackBoxTechnique[]>(['EP', 'BVA', 'DT']);
  const [viewRequirementId, setViewRequirementId] = useState<string>();

  const { blackboxResults, enqueueBlackbox } = useTestDesignJobStore();

  useEffect(() => {
    setListLoading(true);
    void listRequirements()
      .then((rows) => {
        const structured = rows.filter((item) => item.is_structured);
        setRequirements(structured);
      })
      .catch(() => message.error('需求列表加载失败，请先检查后端服务'))
      .finally(() => setListLoading(false));
  }, []);

  const selectedRecords = useMemo(
    () => requirements.filter((r) => selectedRowKeys.includes(r.id)),
    [requirements, selectedRowKeys],
  );

  const mergedResult = useMemo(() => {
    const ids = Object.keys(blackboxResults);
    if (ids.length === 0) return null;
    if (viewRequirementId && blackboxResults[viewRequirementId]) {
      return blackboxResults[viewRequirementId];
    }
    return mergeBlackboxResults(Object.values(blackboxResults));
  }, [blackboxResults, viewRequirementId]);

  const handleGenerate = (records = selectedRecords) => {
    if (records.length === 0) {
      message.warning('请至少选择一条已结构化需求');
      return;
    }
    if (techniques.length === 0) {
      message.warning('请至少选择一种黑盒测试方法');
      return;
    }

    enqueueBlackbox(
      records.map((row) => ({
        internalId: row.id,
        requirement: toStructuredRequirement(row),
        title: getRequirementDisplayName(row),
      })),
      { techniques },
    );
    message.success(`已将 ${records.length} 条需求加入黑盒生成队列`);
  };

  const handleUseForExport = () => {
    if (!mergedResult || mergedResult.test_cases.length === 0) {
      message.warning('请先生成黑盒测试结果');
      return;
    }
    const ids = viewRequirementId ? [viewRequirementId] : Object.keys(blackboxResults);
    saveSuiteForReviewExport(buildSuite(ids, mergedResult));
    message.success('已将当前黑盒结果设为审查导出内容');
  };

  const caseColumns: ColumnsType<TestCase> = [
    { title: '编号', dataIndex: 'id', width: 140 },
    { title: '标题', dataIndex: 'title', ellipsis: true },
    {
      title: '方法',
      dataIndex: 'technique',
      width: 110,
      render: (technique: string) => <Tag>{technique}</Tag>,
    },
    {
      title: '步骤',
      dataIndex: 'test_steps',
      render: (steps: string[]) => steps.join(' → '),
    },
    { title: '预期结果', dataIndex: 'expected_result', ellipsis: true },
  ];

  const coverageColumns: ColumnsType<CoverageItem> = [
    { title: '覆盖项', dataIndex: 'id', width: 180 },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    { title: '类型', dataIndex: 'item_type', width: 140 },
    {
      title: '覆盖用例',
      dataIndex: 'covered_by_test_cases',
      render: (items: string[]) => items.map((item) => <Tag key={item}>{item}</Tag>),
    },
  ];

  const resultSummaryColumns: ColumnsType<RequirementResponse> = [
    {
      title: '需求',
      key: 'title',
      render: (_: unknown, record) => getRequirementDisplayName(record),
    },
    {
      title: '用例数',
      key: 'cases',
      width: 90,
      render: (_: unknown, record) => blackboxResults[record.id]?.test_cases.length ?? '-',
    },
    {
      title: '覆盖率',
      key: 'coverage',
      width: 100,
      render: (_: unknown, record) => {
        const report = blackboxResults[record.id]?.coverage_report;
        return report ? `${report.coverage_percentage.toFixed(1)}%` : '-';
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record) => (
        <Button
          type="link"
          size="small"
          disabled={!blackboxResults[record.id]}
          onClick={() => setViewRequirementId(record.id)}
        >
          查看
        </Button>
      ),
    },
  ];

  const completedIds = Object.keys(blackboxResults);
  const completedRows = requirements.filter((r) => completedIds.includes(r.id));

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div className="section-heading">
        <div>
          <Title level={3}>黑盒测试设计</Title>
          <Text className="muted-text">基于结构化需求生成等价类、边界值和判定表测试用例</Text>
        </div>
      </div>

      <Alert
        showIcon
        type="info"
        message="在下方表格勾选需求，可单条或批量生成黑盒用例；任务在后台队列中执行，不阻塞页面操作。"
      />

      <Card
        title="选择需求"
        extra={
          <Space wrap>
            <Popconfirm
              title={`为选中的 ${selectedRecords.length} 条需求生成黑盒用例？`}
              onConfirm={() => handleGenerate()}
              okText="确认"
              cancelText="取消"
              disabled={selectedRecords.length === 0 || techniques.length === 0}
            >
              <Button
                type="primary"
                disabled={selectedRecords.length === 0 || techniques.length === 0}
              >
                {selectedRecords.length > 1
                  ? `批量生成 (${selectedRecords.length})`
                  : '生成黑盒用例'}
              </Button>
            </Popconfirm>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <Text strong>黑盒测试方法</Text>
            <div style={{ marginTop: 8 }}>
              <Checkbox.Group
                options={techniqueOptions}
                value={techniques}
                onChange={(value) => setTechniques(value as BlackBoxTechnique[])}
              />
            </div>
          </div>
          <StructuredRequirementTable
            requirements={requirements}
            loading={listLoading}
            selectedRowKeys={selectedRowKeys}
            onSelectionChange={setSelectedRowKeys}
          />
        </Space>
      </Card>

      {completedRows.length > 0 && (
        <Card
          title="生成结果"
          extra={
            <Space>
              {viewRequirementId && (
                <Button size="small" onClick={() => setViewRequirementId(undefined)}>
                  查看全部合并
                </Button>
              )}
              <Button disabled={!mergedResult} onClick={handleUseForExport}>
                覆盖审查导出内容
              </Button>
            </Space>
          }
        >
          <Table<RequirementResponse>
            rowKey="id"
            size="small"
            dataSource={completedRows}
            columns={resultSummaryColumns}
            pagination={false}
            style={{ marginBottom: 16 }}
          />
          <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
            {viewRequirementId
              ? `当前查看：${getRequirementDisplayName(requirements.find((r) => r.id === viewRequirementId)!)}`
              : '当前查看：全部需求合并结果'}
            {' · '}
            单独生成黑盒结果不会自动覆盖综合设计结果；需要替换导出内容时再点击覆盖。
          </Text>

          {mergedResult ? (
            <>
              <Row gutter={[16, 16]}>
                <Col xs={12} lg={6}>
                  <div className="tool-panel">
                    <Statistic title="覆盖项总数" value={mergedResult.coverage_report.total_coverage_items} />
                  </div>
                </Col>
                <Col xs={12} lg={6}>
                  <div className="tool-panel">
                    <Statistic title="已覆盖" value={mergedResult.coverage_report.covered_items} />
                  </div>
                </Col>
                <Col xs={12} lg={6}>
                  <div className="tool-panel">
                    <Statistic title="未覆盖" value={mergedResult.coverage_report.uncovered_items} />
                  </div>
                </Col>
                <Col xs={12} lg={6}>
                  <div className="tool-panel">
                    <Statistic
                      title="覆盖率"
                      suffix="%"
                      precision={1}
                      value={mergedResult.coverage_report.coverage_percentage}
                    />
                  </div>
                </Col>
              </Row>

              <Card title="黑盒测试用例" style={{ marginTop: 16 }}>
                <Table<TestCase>
                  rowKey="id"
                  dataSource={mergedResult.test_cases}
                  columns={caseColumns}
                  pagination={{ pageSize: 8 }}
                />
              </Card>

              <Card title="覆盖项追踪" style={{ marginTop: 16 }}>
                <Table<CoverageItem>
                  rowKey="id"
                  dataSource={mergedResult.coverage_items}
                  columns={coverageColumns}
                  pagination={{ pageSize: 8 }}
                />
              </Card>
            </>
          ) : (
            <Empty description="所选需求尚未完成生成" />
          )}
        </Card>
      )}

      {completedRows.length === 0 && (
        <div className="tool-panel">
          <Empty description="暂无黑盒测试结果，请勾选需求并生成" />
        </div>
      )}
    </Space>
  );
}
