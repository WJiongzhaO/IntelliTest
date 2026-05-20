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
  { label: 'EP (C)', value: 'EP' },
  { label: 'BVA (C)', value: 'BVA' },
  { label: 'DT (C)', value: 'DT' },
  { label: 'StateTransition (D)', value: 'StateTransition' },
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
        message.error('Failed to load requirements — complete Structure step first');
      }
    })();
  }, [selectedId]);

  const handleRun = async () => {
    if (!selectedId) {
      message.warning('Select a structured requirement');
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
      message.success(`Suite ${result.id}: ${result.test_cases.length} cases`);
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Pipeline failed');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 120 },
    { title: 'Title', dataIndex: 'title', ellipsis: true },
    {
      title: 'Technique',
      dataIndex: 'technique',
      render: (t: string) => <Tag>{t}</Tag>,
    },
    {
      title: 'Expected',
      dataIndex: 'expected_result',
      ellipsis: true,
      render: (v: string | undefined) => v ?? <Text type="secondary">—</Text>,
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>Combined Test Design (C + D)</Title>
      <Alert
        type="info"
        showIcon
        message="Workflow: Requirements (A) → Structure → Risk (B) → run pipeline here → Oracle Editor for review."
      />

      <Card title="Pipeline options">
        <Form layout="vertical">
          <Form.Item label="Structured requirement">
            <Select
              value={selectedId ?? undefined}
              onChange={setSelectedId}
              options={rows.map((r) => ({
                value: r.id,
                label: `${r.id} (risk=${r.risk_score ?? '—'})`,
              }))}
              placeholder="Select from Requirements page"
            />
          </Form.Item>
          <Form.Item label="Techniques">
            <Checkbox.Group
              options={TECH_OPTIONS}
              value={techniques}
              onChange={(v) => setTechniques(v as string[])}
            />
          </Form.Item>
          <Form.Item label="Whitebox coverage">
            <Select<CoverageCriterion>
              value={coverage}
              onChange={setCoverage}
              options={[
                { value: 'ALL_STATES', label: 'All States' },
                { value: 'ALL_TRANSITIONS', label: 'All Transitions' },
              ]}
            />
          </Form.Item>
          <Space>
            <Switch checked={useLlm} onChange={setUseLlm} /> Use LLM (needs API key)
          </Space>
          <Space>
            <Switch checked={synthesizeOracles} onChange={setSynthesizeOracles} />
            Synthesize oracles (FR 5.0)
          </Space>
          <Button type="primary" loading={loading} onClick={() => void handleRun()}>
            Run combined pipeline
          </Button>
        </Form>
      </Card>

      {suite && (
        <Card title={`Suite ${suite.id} (${suite.test_cases.length} cases)`}>
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
