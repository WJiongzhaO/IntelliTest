import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Checkbox,
  Col,
  Collapse,
  Empty,
  Input,
  List,
  Popconfirm,
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
  DeleteOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  HistoryOutlined,
  PlusOutlined,
  SaveOutlined,
  CompressOutlined,
} from '@ant-design/icons';
import { getReviewArtifacts, saveReviewBundle, type RequirementReviewBundle } from '../api/artifacts';
import { exportArtifact, downloadBlob } from '../api/export';
import BulkExportModal from '../components/BulkExportModal';
import { defaultExportBasename } from '../utils/directoryExport';
import { listRequirements } from '../api/requirements';
import { optimizeSuite } from '../api/suites';
import { REVIEW_HISTORY_STORAGE_KEY } from '../utils/exportSuiteStorage';
import type {
  CoverageItem,
  ExportFormat,
  OptimizationMetrics,
  OptimizationStrategy,
  RequirementResponse,
  ReviewHistoryItem,
  TestCase,
} from '../types/models';
import { getRequirementRefId, toStructuredRequirement } from '../utils/requirementMapper';
import {
  createManualTestCase,
  syncCoverageFromCases,
} from '../utils/reviewCoverageSync';

const { TextArea } = Input;
const { Title, Text } = Typography;
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

function bundleLabel(bundle: RequirementReviewBundle): string {
  const title = bundle.title?.trim();
  if (title) return `${bundle.requirement_ref} · ${title}`;
  return bundle.requirement_ref;
}

function exportBasename(bundle: RequirementReviewBundle): string {
  return defaultExportBasename(bundle);
}

function applyOptimizedCases(
  bundle: RequirementReviewBundle,
  testCases: TestCase[],
): RequirementReviewBundle {
  return {
    ...bundle,
    test_cases: testCases,
    coverage_items: syncCoverageFromCases(bundle.coverage_items, testCases),
  };
}

export default function ReviewExportPage() {
  const [bundles, setBundles] = useState<RequirementReviewBundle[]>([]);
  const [requirements, setRequirements] = useState<RequirementResponse[]>([]);
  const [history, setHistory] = useState<ReviewHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeKeys, setActiveKeys] = useState<string[]>([]);
  const [strategy, setStrategy] = useState<OptimizationStrategy>('risk_then_minimize');
  const [metrics, setMetrics] = useState<OptimizationMetrics | null>(null);
  const [includeRequirements, setIncludeRequirements] = useState(true);
  const [includeCoverage, setIncludeCoverage] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);
  const [bulkExportOpen, setBulkExportOpen] = useState(false);

  const [casePageByReq, setCasePageByReq] = useState<Record<string, number>>({});
  const [casePageSizeByReq, setCasePageSizeByReq] = useState<Record<string, number>>({});

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [artifactData, reqRows] = await Promise.all([
        getReviewArtifacts(),
        listRequirements(),
      ]);
      setBundles(artifactData.bundles);
      setRequirements(reqRows);
      setActiveKeys(artifactData.bundles.map((b) => b.requirement_id));
    } catch {
      message.error('审查数据加载失败，请确认已生成并持久化测试用例');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
    const rawHistory = sessionStorage.getItem(HISTORY_STORAGE_KEY);
    if (rawHistory) {
      try {
        setHistory(JSON.parse(rawHistory) as ReviewHistoryItem[]);
      } catch {
        setHistory([]);
      }
    }
  }, [loadData]);

  const requirementById = useMemo(() => {
    const map = new Map<string, RequirementResponse>();
    for (const item of requirements) {
      map.set(item.id, item);
      const ref = getRequirementRefId(item);
      if (ref !== item.id) map.set(ref, item);
    }
    return map;
  }, [requirements]);

  const totalCases = useMemo(
    () => bundles.reduce((sum, bundle) => sum + bundle.test_cases.length, 0),
    [bundles],
  );

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

  const updateBundle = (
    requirementId: string,
    updater: (bundle: RequirementReviewBundle) => RequirementReviewBundle,
  ) => {
    setBundles((prev) =>
      prev.map((bundle) => (bundle.requirement_id === requirementId ? updater(bundle) : bundle)),
    );
  };

  const updateCase = (requirementId: string, id: string, patch: Partial<TestCase>) => {
    updateBundle(requirementId, (bundle) => {
      const test_cases = bundle.test_cases.map((item) => {
        if (item.id !== id) return item;
        const next = { ...item, ...patch, modified_by_user: true };
        Object.entries(patch).forEach(([field, value]) => {
          recordChange(id, field, String(item[field as keyof TestCase] ?? ''), String(value ?? ''));
        });
        return next;
      });
      const coverageChanged = patch.coverage_items !== undefined;
      return {
        ...bundle,
        test_cases,
        coverage_items: coverageChanged
          ? syncCoverageFromCases(bundle.coverage_items, test_cases)
          : bundle.coverage_items,
      };
    });
  };

  const addCase = (requirementId: string) => {
    updateBundle(requirementId, (bundle) => {
      const newCase = createManualTestCase(bundle.requirement_ref, bundle.test_cases);
      recordChange(newCase.id, 'created', '-', newCase.title);
      const test_cases = [...bundle.test_cases, newCase];
      return {
        ...bundle,
        test_cases,
        coverage_items: syncCoverageFromCases(bundle.coverage_items, test_cases),
      };
    });
    message.success('已新增用例，请编辑后保存');
  };

  const removeCase = (requirementId: string, caseId: string) => {
    updateBundle(requirementId, (bundle) => {
      const test_cases = bundle.test_cases.filter((item) => item.id !== caseId);
      recordChange(caseId, 'deleted', caseId, '-');
      return {
        ...bundle,
        test_cases,
        coverage_items: syncCoverageFromCases(bundle.coverage_items, test_cases),
      };
    });
    message.success('用例已删除');
  };

  const updateCoverage = (requirementId: string, id: string, patch: Partial<CoverageItem>) => {
    updateBundle(requirementId, (bundle) => ({
      ...bundle,
      coverage_items: bundle.coverage_items.map((item) => {
        if (item.id !== id) return item;
        const next = { ...item, ...patch };
        Object.entries(patch).forEach(([field, value]) => {
          recordChange(id, field, String(item[field as keyof CoverageItem] ?? ''), String(value ?? ''));
        });
        return next;
      }),
    }));
  };

  const persistAll = async () => {
    if (bundles.length === 0) {
      message.warning('没有可保存的审查数据');
      return;
    }
    try {
      await Promise.all(
        bundles.map((bundle) =>
          saveReviewBundle(bundle.requirement_id, bundle.test_cases, bundle.coverage_items),
        ),
      );
      message.success('全部审查结果已保存到数据库');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存失败');
    }
  };

  const handleOptimizeBundle = async (bundle: RequirementReviewBundle) => {
    if (!bundle.test_cases.length) return;
    try {
      const result = await optimizeSuite(
        bundle.test_cases,
        strategy,
        bundle.coverage_items.map((item) => item.id),
      );
      updateBundle(bundle.requirement_id, (current) =>
        applyOptimizedCases(current, result.optimized_test_cases),
      );
      setMetrics(result.metrics);
      message.success(`${bundle.requirement_ref} 套件优化完成`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '套件优化失败');
    }
  };

  const handleOptimizeAll = async () => {
    if (bundles.length === 0) {
      message.warning('没有可优化的需求套件');
      return;
    }
    setExporting('all-optimize');
    let totalBefore = 0;
    let totalAfter = 0;
    try {
      const nextBundles: RequirementReviewBundle[] = [];
      for (const bundle of bundles) {
        if (!bundle.test_cases.length) {
          nextBundles.push(bundle);
          continue;
        }
        const result = await optimizeSuite(
          bundle.test_cases,
          strategy,
          bundle.coverage_items.map((item) => item.id),
        );
        totalBefore += result.metrics.case_count_before;
        totalAfter += result.metrics.case_count_after;
        nextBundles.push(applyOptimizedCases(bundle, result.optimized_test_cases));
        setMetrics(result.metrics);
      }
      setBundles(nextBundles);
      message.success(`全部优化完成：${totalBefore} → ${totalAfter} 条用例`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '批量优化失败');
    } finally {
      setExporting(null);
    }
  };

  const buildArtifactForBundle = (bundle: RequirementReviewBundle, basename?: string) => {
    const reqRow = requirementById.get(bundle.requirement_id);
    const structured = reqRow ? [toStructuredRequirement(reqRow)] : [];
    return {
      suite: bundle.suite ?? {
        id: `review-${bundle.requirement_id}`,
        name: bundle.suite?.name ?? `Combined design for ${bundleLabel(bundle)}`,
        test_cases: bundle.test_cases,
      },
      requirements: includeRequirements ? structured : [],
      test_cases: bundle.test_cases,
      coverage_items: includeCoverage ? bundle.coverage_items : [],
      options: {
        include_requirements: includeRequirements,
        include_test_cases: true,
        include_coverage: includeCoverage,
        include_summary: true,
        file_basename: basename ?? exportBasename(bundle),
      },
    };
  };

  const handleExportBundle = async (bundle: RequirementReviewBundle, fileFormat: ExportFormat) => {
    const key = `${bundle.requirement_id}-${fileFormat}`;
    setExporting(key);
    try {
      const blob = await exportArtifact(buildArtifactForBundle(bundle), fileFormat);
      downloadBlob(blob, `${exportBasename(bundle)}.${fileFormat}`);
      message.success(`${exportBasename(bundle)}.${fileFormat} 导出完成`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '导出失败');
    } finally {
      setExporting(null);
    }
  };

  const openBulkExport = () => {
    if (bundles.length === 0) {
      message.warning('没有可导出的需求套件');
      return;
    }
    setBulkExportOpen(true);
  };

  const buildCaseColumns = (requirementId: string): ColumnsType<TestCase> => [
    {
      title: '用例',
      dataIndex: 'title',
      width: 240,
      render: (_, row) => (
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Text strong>{row.id}</Text>
          <Input value={row.title} onChange={(e) => updateCase(requirementId, row.id, { title: e.target.value })} />
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
            onChange={(e) =>
              updateCase(requirementId, row.id, {
                test_steps: e.target.value.split('\n').filter((line) => line.trim()),
              })
            }
          />
          <Input
            placeholder="测试数据"
            value={row.test_data}
            onChange={(e) => updateCase(requirementId, row.id, { test_data: e.target.value })}
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
          onChange={(e) => updateCase(requirementId, row.id, { expected_result: e.target.value })}
        />
      ),
    },
    {
      title: '追溯',
      width: 180,
      render: (_, row) => (
        <Space direction="vertical" size={6}>
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
            onChange={(priority: TestCase['priority']) => updateCase(requirementId, row.id, { priority })}
          />
          {row.modified_by_user && <Tag color="blue">已人工修改</Tag>}
        </Space>
      ),
    },
    {
      title: '操作',
      width: 56,
      fixed: 'right',
      render: (_, row) => (
        <Popconfirm
          title="删除此用例？"
          description="覆盖项关联将同步更新"
          onConfirm={() => removeCase(requirementId, row.id)}
        >
          <Button size="small" danger type="text" icon={<DeleteOutlined />} aria-label="删除用例" />
        </Popconfirm>
      ),
    },
  ];

  const buildCoverageColumns = (requirementId: string): ColumnsType<CoverageItem> => [
    { title: '覆盖项', dataIndex: 'id', width: 180 },
    {
      title: '描述',
      dataIndex: 'description',
      render: (_, row) => (
        <Input
          value={row.description}
          onChange={(e) => updateCoverage(requirementId, row.id, { description: e.target.value })}
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
          onChange={(e) => updateCoverage(requirementId, row.id, { item_type: e.target.value })}
        />
      ),
    },
    {
      title: '覆盖用例',
      dataIndex: 'covered_by_test_cases',
      render: (items: string[]) => items.map((item) => <Tag key={item}>{item}</Tag>),
    },
  ];

  const collapseItems = bundles.map((bundle) => ({
    key: bundle.requirement_id,
    label: (
      <Space>
        <Text strong>{bundleLabel(bundle)}</Text>
        <Tag>{bundle.test_cases.length} 条用例</Tag>
      </Space>
    ),
    children: (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Space wrap>
          <Button size="small" icon={<PlusOutlined />} onClick={() => addCase(bundle.requirement_id)}>
            新增用例
          </Button>
          <Button size="small" icon={<CompressOutlined />} onClick={() => void handleOptimizeBundle(bundle)}>
            优化本需求套件
          </Button>
          <Button
            size="small"
            icon={<FileTextOutlined />}
            loading={exporting === `${bundle.requirement_id}-json`}
            onClick={() => void handleExportBundle(bundle, 'json')}
          >
            导出 JSON
          </Button>
          <Button
            size="small"
            icon={<FileTextOutlined />}
            loading={exporting === `${bundle.requirement_id}-csv`}
            onClick={() => void handleExportBundle(bundle, 'csv')}
          >
            CSV
          </Button>
          <Button
            size="small"
            icon={<FileExcelOutlined />}
            loading={exporting === `${bundle.requirement_id}-xlsx`}
            onClick={() => void handleExportBundle(bundle, 'xlsx')}
          >
            Excel
          </Button>
        </Space>
        <Table<TestCase>
          rowKey="id"
          dataSource={bundle.test_cases}
          columns={buildCaseColumns(bundle.requirement_id)}
          pagination={{
            current: casePageByReq[bundle.requirement_id] ?? 1,
            pageSize: casePageSizeByReq[bundle.requirement_id] ?? 5,
            showSizeChanger: true,
            pageSizeOptions: [5, 10, 20, 50],
            onChange: (page, pageSize) => {
              setCasePageByReq((prev) => ({ ...prev, [bundle.requirement_id]: page }));
              setCasePageSizeByReq((prev) => ({ ...prev, [bundle.requirement_id]: pageSize }));
            },
          }}
          scroll={{ x: 980 }}
        />
        <Table<CoverageItem>
          rowKey="id"
          size="small"
          dataSource={bundle.coverage_items}
          columns={buildCoverageColumns(bundle.requirement_id)}
          pagination={{ pageSize: 5 }}
        />
      </Space>
    ),
  }));

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div className="section-heading">
        <div>
          <Title level={3}>交互式审查与导出</Title>
          <Text className="muted-text">按需求查看、编辑并分别导出测试用例（数据来自数据库）</Text>
        </div>
        <Space wrap>
          <Button icon={<SaveOutlined />} onClick={() => void persistAll()}>
            保存全部审查
          </Button>
          <Button
            icon={<CompressOutlined />}
            loading={exporting === 'all-optimize'}
            onClick={() => void handleOptimizeAll()}
          >
            优化全部套件
          </Button>
          <Button type="primary" icon={<FileExcelOutlined />} onClick={openBulkExport}>
            批量导出
          </Button>
          <Button onClick={() => void loadData()} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      <div className="tool-panel">
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={10}>
            <Space direction="vertical">
              <Text strong>导出范围</Text>
              <Checkbox checked disabled>
                测试用例
              </Checkbox>
              <Checkbox checked={includeRequirements} onChange={(e) => setIncludeRequirements(e.target.checked)}>
                需求与风险
              </Checkbox>
              <Checkbox checked={includeCoverage} onChange={(e) => setIncludeCoverage(e.target.checked)}>
                覆盖项
              </Checkbox>
            </Space>
          </Col>
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
          <Col xs={24} lg={6}>
            <div className="metric-tile">
              <span>{totalCases}</span>
              <Text>待审查用例（{bundles.length} 条需求）</Text>
            </div>
          </Col>
        </Row>
        {metrics && (
          <div className="optimizer-summary" style={{ marginTop: 16 }}>
            <Tag color="blue">{strategyLabels[metrics.strategy_applied]}</Tag>
            <Text>
              用例数 {metrics.case_count_before} → {metrics.case_count_after}
            </Text>
          </div>
        )}
      </div>

      <div className="tool-panel">
        <div className="panel-title">
          <AuditOutlined />
          <Text strong>按需求审查</Text>
        </div>
        {bundles.length > 0 ? (
          <Collapse activeKey={activeKeys} onChange={(keys) => setActiveKeys(keys as string[])} items={collapseItems} />
        ) : (
          <Empty description="暂无持久化测试用例，请先在综合设计/黑盒/白盒页面生成" />
        )}
      </div>

      <BulkExportModal
        open={bulkExportOpen}
        bundles={bundles}
        buildArtifact={(bundle, basename) => buildArtifactForBundle(bundle, basename)}
        onClose={() => setBulkExportOpen(false)}
      />

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
