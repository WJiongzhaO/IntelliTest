import { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Checkbox,
  Col,
  Empty,
  Input,
  List,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  AuditOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  HistoryOutlined,
  SaveOutlined,
  CompressOutlined,
} from '@ant-design/icons';
import { exportArtifact, downloadBlob } from '../api/export';
import { listRequirements } from '../api/requirements';
import { optimizeSuite } from '../api/suites';
import { SUITE_STORAGE_KEY } from './TestDesignWorkbench';
import { REVIEW_HISTORY_STORAGE_KEY, REVIEW_SUITE_STORAGE_KEY } from '../utils/exportSuiteStorage';
import type {
  CoverageItem,
  ExportArtifact,
  ExportFormat,
  RequirementResponse,
  ReviewHistoryItem,
  TestCase,
  TestSuite,
  OptimizationMetrics,
  OptimizationStrategy,
} from '../types/models';
import { getRequirementDisplayName, toStructuredRequirement } from '../utils/requirementMapper';

const { TextArea } = Input;
const { Title, Text } = Typography;

const REVIEW_STORAGE_KEY = REVIEW_SUITE_STORAGE_KEY;
const HISTORY_STORAGE_KEY = REVIEW_HISTORY_STORAGE_KEY;

const priorityLabels: Record<string, string> = {
  High: '高',
  Medium: '中',
  Low: '低',
};

const strategyLabels: Record<OptimizationStrategy, string> = {
  risk_sort: '按风险排序',
  minimize_coverage: '覆盖最小化',
  risk_then_minimize: '风险优先 + 覆盖最小化',
};

function buildCoverageFromCases(cases: TestCase[]): CoverageItem[] {
  const coverageMap = new Map<string, CoverageItem>();
  cases.forEach((testCase) => {
    testCase.coverage_items.forEach((coverageId) => {
      const existing = coverageMap.get(coverageId);
      if (existing) {
        coverageMap.set(coverageId, {
          ...existing,
          covered_by_test_cases: [...new Set([...existing.covered_by_test_cases, testCase.id])],
        });
        return;
      }
      coverageMap.set(coverageId, {
        id: coverageId,
        requirement_id: testCase.requirement_id,
        description: coverageId,
        item_type: testCase.technique === 'StateTransition' ? 'state_transition' : 'blackbox',
        selected_techniques:
          testCase.technique && testCase.technique !== 'StateTransition' ? [testCase.technique] : [],
        covered_by_test_cases: [testCase.id],
      });
    });
  });
  return Array.from(coverageMap.values());
}

function parseStoredSuite(): TestSuite | null {
  const reviewed = sessionStorage.getItem(REVIEW_STORAGE_KEY);
  const generated = sessionStorage.getItem(SUITE_STORAGE_KEY);
  const raw = reviewed ?? generated;
  if (!raw) return null;
  try {
    return JSON.parse(raw) as TestSuite;
  } catch {
    return null;
  }
}

export default function ReviewExportPage() {
  const [suite, setSuite] = useState<TestSuite | null>(null);
  const [cases, setCases] = useState<TestCase[]>([]);
  const [requirements, setRequirements] = useState<RequirementResponse[]>([]);
  const [coverageItems, setCoverageItems] = useState<CoverageItem[]>([]);
  const [history, setHistory] = useState<ReviewHistoryItem[]>([]);
  const [fileBasename, setFileBasename] = useState('intellitest_test_artifacts');
  const [strategy, setStrategy] = useState<OptimizationStrategy>('risk_then_minimize');
  const [metrics, setMetrics] = useState<OptimizationMetrics | null>(null);
  const [includeRequirements, setIncludeRequirements] = useState(true);
  const [includeCoverage, setIncludeCoverage] = useState(true);
  const [exporting, setExporting] = useState<ExportFormat | null>(null);

  useEffect(() => {
    const currentSuite = parseStoredSuite();
    if (currentSuite) {
      setSuite(currentSuite);
      setCases(currentSuite.test_cases);
      setCoverageItems(buildCoverageFromCases(currentSuite.test_cases));
    }

    const rawHistory = sessionStorage.getItem(HISTORY_STORAGE_KEY);
    if (rawHistory) {
      try {
        setHistory(JSON.parse(rawHistory) as ReviewHistoryItem[]);
      } catch {
        setHistory([]);
      }
    }

    void listRequirements()
      .then(setRequirements)
      .catch(() => message.warning('需求列表暂时不可用，仍可导出当前测试套件'));
  }, []);

  const reviewedSuite = useMemo<TestSuite | null>(() => {
    if (!suite) return null;
    return { ...suite, test_cases: cases };
  }, [suite, cases]);

  const requirementNameById = useMemo(() => {
    const entries = requirements.map((item) => [item.id, getRequirementDisplayName(item)] as const);
    return new Map(entries);
  }, [requirements]);

  const recordChange = (target: string, field: string, before: string, after: string) => {
    if (before === after) return;
    const item: ReviewHistoryItem = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      target,
      field,
      before,
      after,
      created_at: new Date().toLocaleString(),
    };
    setHistory((prev) => {
      const next = [item, ...prev].slice(0, 30);
      sessionStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const updateCase = (id: string, patch: Partial<TestCase>) => {
    setCases((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item;
        const next = { ...item, ...patch, modified_by_user: true };
        Object.entries(patch).forEach(([field, value]) => {
          recordChange(id, field, String(item[field as keyof TestCase] ?? ''), String(value ?? ''));
        });
        return next;
      }),
    );
  };

  const updateCoverage = (id: string, patch: Partial<CoverageItem>) => {
    setCoverageItems((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item;
        const next = { ...item, ...patch };
        Object.entries(patch).forEach(([field, value]) => {
          recordChange(id, field, String(item[field as keyof CoverageItem] ?? ''), String(value ?? ''));
        });
        return next;
      }),
    );
  };

  const persistReview = () => {
    if (!reviewedSuite) {
      message.warning('当前没有可保存的测试套件');
      return;
    }
    sessionStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify(reviewedSuite));
    message.success('审查结果已保存到当前浏览器会话');
  };

  const handleOptimize = async () => {
    if (!cases.length) {
      message.warning('当前没有可优化的测试用例');
      return;
    }
    try {
      const result = await optimizeSuite(
        cases,
        strategy,
        coverageItems.map((item) => item.id),
      );
      setCases(result.optimized_test_cases);
      setMetrics(result.metrics);
      message.success('测试套件优化完成');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '套件优化失败');
    }
  };

  const handleExport = async (fileFormat: ExportFormat) => {
    const artifact: ExportArtifact = {
      suite: reviewedSuite,
      requirements: includeRequirements ? requirements.map(toStructuredRequirement) : [],
      test_cases: cases,
      coverage_items: includeCoverage ? coverageItems : [],
      options: {
        include_requirements: includeRequirements,
        include_test_cases: true,
        include_coverage: includeCoverage,
        include_summary: true,
        file_basename: fileBasename,
      },
    };

    setExporting(fileFormat);
    try {
      const blob = await exportArtifact(artifact, fileFormat);
      downloadBlob(blob, `${fileBasename}.${fileFormat}`);
      message.success(`${fileFormat.toUpperCase()} 导出完成`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '导出失败');
    } finally {
      setExporting(null);
    }
  };

  const caseColumns: ColumnsType<TestCase> = [
    {
      title: '用例',
      dataIndex: 'title',
      width: 240,
      render: (_, row) => (
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Text strong>{row.id}</Text>
          <Input value={row.title} onChange={(event) => updateCase(row.id, { title: event.target.value })} />
        </Space>
      ),
    },
    {
      title: '步骤 / 数据',
      dataIndex: 'test_steps',
      render: (_, row) => (
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
          <TextArea
            rows={3}
            value={row.test_steps.join('\n')}
            onChange={(event) =>
              updateCase(row.id, {
                test_steps: event.target.value.split('\n').filter((line) => line.trim()),
              })
            }
          />
          <Input
            placeholder="测试数据"
            value={row.test_data}
            onChange={(event) => updateCase(row.id, { test_data: event.target.value })}
          />
        </Space>
      ),
    },
    {
      title: '预期结果',
      dataIndex: 'expected_result',
      render: (_, row) => (
        <TextArea
          rows={3}
          value={row.expected_result}
          onChange={(event) => updateCase(row.id, { expected_result: event.target.value })}
        />
      ),
    },
    {
      title: '追溯',
      width: 180,
      render: (_, row) => (
        <Space direction="vertical" size={6}>
          <Text>{requirementNameById.get(row.requirement_id) ?? row.requirement_id}</Text>
          <Tag>{row.technique ?? '人工'}</Tag>
          <Select
            size="small"
            value={row.priority}
            style={{ width: 112 }}
            options={[
              { value: 'High', label: priorityLabels.High },
              { value: 'Medium', label: priorityLabels.Medium },
              { value: 'Low', label: priorityLabels.Low },
            ]}
            onChange={(priority: TestCase['priority']) => updateCase(row.id, { priority })}
          />
          {row.modified_by_user && <Tag color="blue">已人工修改</Tag>}
        </Space>
      ),
    },
  ];

  const coverageColumns: ColumnsType<CoverageItem> = [
    { title: '覆盖项', dataIndex: 'id', width: 180 },
    {
      title: '需求',
      dataIndex: 'requirement_id',
      width: 180,
      render: (id: string) => requirementNameById.get(id) ?? id,
    },
    {
      title: '描述',
      dataIndex: 'description',
      render: (_, row) => (
        <Input
          value={row.description}
          onChange={(event) => updateCoverage(row.id, { description: event.target.value })}
        />
      ),
    },
    {
      title: '类型',
      dataIndex: 'item_type',
      width: 160,
      render: (_, row) => (
        <Input
          value={row.item_type}
          onChange={(event) => updateCoverage(row.id, { item_type: event.target.value })}
        />
      ),
    },
    {
      title: '覆盖用例',
      dataIndex: 'covered_by_test_cases',
      render: (items: string[]) => items.map((item) => <Tag key={item}>{item}</Tag>),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div className="section-heading">
        <div>
          <Title level={3}>交互式审查与导出</Title>
          <Text className="muted-text">审查测试用例、覆盖项并导出交付物</Text>
        </div>
        <Space wrap>
          <Button icon={<SaveOutlined />} onClick={persistReview}>
            保存审查
          </Button>
          <Button
            icon={<CompressOutlined />}
            onClick={() => void handleOptimize()}
          >
            优化套件
          </Button>
          <Button
            icon={<FileTextOutlined />}
            loading={exporting === 'json'}
            onClick={() => void handleExport('json')}
          >
            JSON
          </Button>
          <Button
            icon={<FileTextOutlined />}
            loading={exporting === 'csv'}
            onClick={() => void handleExport('csv')}
          >
            CSV
          </Button>
          <Button
            type="primary"
            icon={<FileExcelOutlined />}
            loading={exporting === 'xlsx'}
            onClick={() => void handleExport('xlsx')}
          >
            Excel
          </Button>
        </Space>
      </div>

      <div className="tool-panel">
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>导出文件名</Text>
              <Input value={fileBasename} onChange={(event) => setFileBasename(event.target.value)} />
            </Space>
          </Col>
          <Col xs={24} lg={10}>
            <Space direction="vertical">
              <Text strong>导出范围</Text>
              <Checkbox checked disabled>
                测试用例
              </Checkbox>
              <Checkbox checked={includeRequirements} onChange={(event) => setIncludeRequirements(event.target.checked)}>
                需求与风险
              </Checkbox>
              <Checkbox checked={includeCoverage} onChange={(event) => setIncludeCoverage(event.target.checked)}>
                覆盖项
              </Checkbox>
            </Space>
          </Col>
          <Col xs={24} lg={6}>
            <div className="metric-tile">
              <span>{cases.length}</span>
              <Text>待导出用例</Text>
            </div>
          </Col>
        </Row>
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={8}>
            <Text strong>优化策略</Text>
            <Select<OptimizationStrategy>
              style={{ width: '100%', marginTop: 8 }}
              value={strategy}
              onChange={setStrategy}
              options={[
                { value: 'risk_sort', label: '按风险排序' },
                { value: 'minimize_coverage', label: '覆盖最小化' },
                { value: 'risk_then_minimize', label: '风险优先 + 覆盖最小化' },
              ]}
            />
          </Col>
          <Col xs={24} lg={16}>
            {metrics && (
              <div className="optimizer-summary">
                <Tag color="blue">{strategyLabels[metrics.strategy_applied]}</Tag>
                <Text>
                  用例数 {metrics.case_count_before} → {metrics.case_count_after}
                </Text>
                <Text>
                  覆盖率 {(metrics.coverage_ratio_before * 100).toFixed(0)}% →{' '}
                  {(metrics.coverage_ratio_after * 100).toFixed(0)}%
                </Text>
              </div>
            )}
          </Col>
        </Row>
      </div>

      <div className="tool-panel">
        <div className="panel-title">
          <AuditOutlined />
          <Text strong>测试用例审查</Text>
        </div>
        {cases.length ? (
          <Table<TestCase>
            rowKey="id"
            dataSource={cases}
            columns={caseColumns}
            pagination={{ pageSize: 5 }}
            scroll={{ x: 980 }}
          />
        ) : (
          <Empty description="请先在测试设计工作台生成测试套件" />
        )}
      </div>

      <div className="tool-panel">
        <div className="panel-title">
          <DownloadOutlined />
          <Text strong>覆盖项审查</Text>
        </div>
        <Table<CoverageItem>
          rowKey="id"
          dataSource={coverageItems}
          columns={coverageColumns}
          pagination={{ pageSize: 5 }}
        />
      </div>

      <div className="tool-panel">
        <div className="panel-title">
          <HistoryOutlined />
          <Text strong>修改历史</Text>
        </div>
        <List
          dataSource={history}
          locale={{ emptyText: '暂无人工修改记录' }}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                title={`${item.target} · ${item.field}`}
                description={`${item.before || '-'} → ${item.after || '-'} · ${item.created_at}`}
              />
            </List.Item>
          )}
        />
      </div>
    </Space>
  );
}
