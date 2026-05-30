import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { listRequirements } from '../api/requirements';
import StructuredRequirementTable from '../components/StructuredRequirementTable';
import { useTestDesignJobStore } from '../stores/testDesignJobStore';
import type {
  CoverageCriterion,
  RequirementResponse,
  TestCase,
  TestSuite,
} from '../types/models';
import { saveSuiteForReviewExport } from '../utils/exportSuiteStorage';
import { getRequirementDisplayName, toStructuredRequirement } from '../utils/requirementMapper';

const { Title, Text } = Typography;

const TECH_OPTIONS = [
  { label: '等价类划分（EP）', value: 'EP' },
  { label: '边界值分析（BVA）', value: 'BVA' },
  { label: '判定表（DT）', value: 'DT' },
  { label: '状态转换', value: 'StateTransition' },
];

const coverageOptions = [
  { value: 'ALL_STATES', label: '全部状态' },
  { value: 'ALL_TRANSITIONS', label: '全部转换' },
];

function TestDesignWorkbench() {
  const [rows, setRows] = useState<RequirementResponse[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [techniques, setTechniques] = useState<string[]>(['EP', 'BVA', 'DT', 'StateTransition']);
  const [coverage, setCoverage] = useState<CoverageCriterion>('ALL_TRANSITIONS');
  const [useLlm, setUseLlm] = useState(true);
  const [synthesizeOracles, setSynthesizeOracles] = useState(true);
  const [viewRequirementId, setViewRequirementId] = useState<string>();

  const { combinedResults, enqueueCombined } = useTestDesignJobStore();

  useEffect(() => {
    setListLoading(true);
    void listRequirements()
      .then((data) => setRows(data.filter((r) => r.is_structured)))
      .catch(() => message.error('需求加载失败，请先完成结构化步骤'))
      .finally(() => setListLoading(false));
  }, []);

  const selectedRecords = useMemo(
    () => rows.filter((r) => selectedRowKeys.includes(r.id)),
    [rows, selectedRowKeys],
  );

  const completedIds = Object.keys(combinedResults);
  const completedRows = rows.filter((r) => completedIds.includes(r.id));

  const mergedSuite = useMemo((): TestSuite | null => {
    const suites = Object.values(combinedResults);
    if (suites.length === 0) return null;
    if (viewRequirementId && combinedResults[viewRequirementId]) {
      return combinedResults[viewRequirementId];
    }
    return {
      id: `combined-view-${Date.now()}`,
      name: '综合测试套件（合并查看）',
      description: `合并 ${suites.length} 条需求的综合设计结果`,
      test_cases: suites.flatMap((s) => s.test_cases),
      created_at: new Date().toISOString(),
    };
  }, [combinedResults, viewRequirementId]);

  const handleRun = (records = selectedRecords) => {
    if (records.length === 0) {
      message.warning('请至少选择一条已结构化的需求');
      return;
    }
    if (techniques.length === 0) {
      message.warning('请至少选择一种测试设计方法');
      return;
    }

    enqueueCombined(
      records.map((row) => ({
        internalId: row.id,
        requirement: toStructuredRequirement(row),
        title: getRequirementDisplayName(row),
      })),
      { techniques, coverage, useLlm, synthesizeOracles },
    );
    message.success(`已将 ${records.length} 条需求加入综合设计队列`);
  };

  const handleSaveForExport = () => {
    if (!mergedSuite) {
      message.warning('请先生成综合设计结果');
      return;
    }
    saveSuiteForReviewExport(mergedSuite);
    message.success('已将当前综合设计结果设为审查导出内容');
  };

  const columns = [
    { title: '编号', dataIndex: 'id', width: 120 },
    { title: '标题', dataIndex: 'title', ellipsis: true },
    {
      title: '方法',
      dataIndex: 'technique',
      render: (t: string) => <Tag>{t}</Tag>,
    },
    {
      title: '预期结果',
      dataIndex: 'expected_result',
      ellipsis: true,
      render: (v: string | undefined) => v ?? <Text type="secondary">-</Text>,
    },
  ];

  const resultSummaryColumns = [
    {
      title: '需求',
      key: 'title',
      render: (_: unknown, record: RequirementResponse) => getRequirementDisplayName(record),
    },
    {
      title: '用例数',
      key: 'cases',
      width: 90,
      render: (_: unknown, record: RequirementResponse) =>
        combinedResults[record.id]?.test_cases.length ?? '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: RequirementResponse) => (
        <Button
          type="link"
          size="small"
          disabled={!combinedResults[record.id]}
          onClick={() => setViewRequirementId(record.id)}
        >
          查看
        </Button>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>综合测试设计</Title>
      <Alert
        type="info"
        showIcon
        message="在下方表格勾选需求，可单条或批量运行综合流程；任务在后台队列中执行，批量完成后自动合并写入审查导出。"
      />

      <Card
        title="选择需求与生成选项"
        extra={
          <Popconfirm
            title={`为选中的 ${selectedRecords.length} 条需求运行综合设计？`}
            onConfirm={() => handleRun()}
            okText="确认"
            cancelText="取消"
            disabled={selectedRecords.length === 0 || techniques.length === 0}
          >
            <Button
              type="primary"
              disabled={selectedRecords.length === 0 || techniques.length === 0}
            >
              {selectedRecords.length > 1
                ? `批量运行 (${selectedRecords.length})`
                : '运行综合流程'}
            </Button>
          </Popconfirm>
        }
      >
        <Form layout="vertical">
          <Form.Item label="测试设计方法">
            <Checkbox.Group
              options={TECH_OPTIONS}
              value={techniques}
              onChange={(v) => setTechniques(v as string[])}
            />
            <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
              判定表（DT）与等价类、边界值会覆盖不同场景；综合流程生成时会按覆盖项合并重复用例，审查阶段可用「风险优先 + 覆盖最小化」进一步精简。
            </Text>
          </Form.Item>
          <Form.Item label="白盒覆盖准则">
            <Select<CoverageCriterion>
              value={coverage}
              onChange={setCoverage}
              options={coverageOptions}
              style={{ maxWidth: 280 }}
            />
          </Form.Item>
          <Space wrap style={{ marginBottom: 16 }}>
            <Space>
              <Switch checked={useLlm} onChange={setUseLlm} /> 使用大模型抽取
            </Space>
            <Space>
              <Switch checked={synthesizeOracles} onChange={setSynthesizeOracles} />
              同步生成测试预言
            </Space>
          </Space>
        </Form>
        <StructuredRequirementTable
          requirements={rows}
          loading={listLoading}
          selectedRowKeys={selectedRowKeys}
          onSelectionChange={setSelectedRowKeys}
        />
      </Card>

      {completedRows.length > 0 && mergedSuite && (
        <Card
          title={`测试套件（${mergedSuite.test_cases.length} 条用例）`}
          extra={
            <Space>
              {viewRequirementId && (
                <Button size="small" onClick={() => setViewRequirementId(undefined)}>
                  查看全部合并
                </Button>
              )}
              <Button onClick={handleSaveForExport}>覆盖审查导出内容</Button>
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
              ? `当前查看：${getRequirementDisplayName(rows.find((r) => r.id === viewRequirementId)!)}`
              : '当前查看：全部需求合并结果'}
          </Text>
          <Table<TestCase>
            rowKey="id"
            dataSource={mergedSuite.test_cases}
            columns={columns}
            pagination={{ pageSize: 10 }}
          />
        </Card>
      )}
    </Space>
  );
}

export default TestDesignWorkbench;

export { EXPORT_SUITE_STORAGE_KEY as SUITE_STORAGE_KEY } from '../utils/exportSuiteStorage';
