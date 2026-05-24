import { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { listRequirements } from '../api/requirements';
import { runCombinedDesign } from '../api/testDesign';
import type {
  CoverageCriterion,
  RequirementResponse,
  TestCase,
  TestSuite,
} from '../types/models';
import { toStructuredRequirement } from '../utils/requirementMapper';

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

const SUITE_STORAGE_KEY = 'intellitest_last_suite';

function TestDesignWorkbench() {
  const [rows, setRows] = useState<RequirementResponse[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [techniques, setTechniques] = useState<string[]>(['EP', 'BVA', 'StateTransition']);
  const [coverage, setCoverage] = useState<CoverageCriterion>('ALL_TRANSITIONS');
  const [useLlm, setUseLlm] = useState(false);
  const [synthesizeOracles, setSynthesizeOracles] = useState(true);
  const [suite, setSuite] = useState<TestSuite | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const data = await listRequirements();
        setRows(data.filter((r) => r.is_structured));
        if (data.length > 0 && !selectedId) {
          const first = data.find((r) => r.is_structured);
          if (first) setSelectedId(first.id);
        }
      } catch {
        message.error('需求加载失败，请先完成结构化步骤');
      }
    })();
  }, [selectedId]);

  const handleRun = async () => {
    if (!selectedId) {
      message.warning('请选择一条已结构化的需求');
      return;
    }
    const row = rows.find((r) => r.id === selectedId);
    if (!row) return;

    setLoading(true);
    try {
      const result = await runCombinedDesign({
        requirement_id: selectedId,
        requirement: toStructuredRequirement(row),
        techniques,
        coverage,
        synthesize_oracles: synthesizeOracles,
        use_llm: useLlm,
      });
      setSuite(result);
      sessionStorage.setItem(SUITE_STORAGE_KEY, JSON.stringify(result));
      message.success(`测试套件 ${result.id} 已生成，共 ${result.test_cases.length} 条用例`);
    } catch (err) {
      message.error(err instanceof Error ? err.message : '综合流程执行失败');
    } finally {
      setLoading(false);
    }
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

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>综合测试设计</Title>
      <Alert
        type="info"
        showIcon
        message="推荐流程：录入需求 → 结构化 → 风险分析 → 生成测试套件 → 测试预言审查。"
      />

      <Card title="生成选项">
        <Form layout="vertical">
          <Form.Item label="已结构化需求">
            <Select
              value={selectedId ?? undefined}
              onChange={setSelectedId}
              options={rows.map((r) => ({
                value: r.id,
                label: `${r.id}（风险=${r.risk_score ?? '-'}）`,
              }))}
              placeholder="从需求列表中选择"
            />
          </Form.Item>
          <Form.Item label="测试设计方法">
            <Checkbox.Group
              options={TECH_OPTIONS}
              value={techniques}
              onChange={(v) => setTechniques(v as string[])}
            />
          </Form.Item>
          <Form.Item label="白盒覆盖准则">
            <Select<CoverageCriterion>
              value={coverage}
              onChange={setCoverage}
              options={coverageOptions}
            />
          </Form.Item>
          <Space>
            <Switch checked={useLlm} onChange={setUseLlm} /> 使用大模型抽取
          </Space>
          <Space>
            <Switch checked={synthesizeOracles} onChange={setSynthesizeOracles} />
            同步生成测试预言
          </Space>
          <Button type="primary" loading={loading} onClick={() => void handleRun()}>
            运行综合流程
          </Button>
        </Form>
      </Card>

      {suite && (
        <Card title={`测试套件 ${suite.id}（${suite.test_cases.length} 条用例）`}>
          <Table<TestCase>
            rowKey="id"
            dataSource={suite.test_cases}
            columns={columns}
            pagination={{ pageSize: 10 }}
          />
        </Card>
      )}
    </Space>
  );
}

export default TestDesignWorkbench;

export { SUITE_STORAGE_KEY };
