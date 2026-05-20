import { useCallback, useEffect, useId, useRef, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import mermaid from 'mermaid';
import type { ColumnsType } from 'antd/es/table';
import {
  createWhiteboxModel,
  regenerateMermaid,
  updateWhiteboxModel,
} from '../api/whitebox';
import type {
  CoverageCriterion,
  StateMachineModel,
  StructuredRequirement,
  TestCase,
  TestSequence,
} from '../types/models';

const { TextArea } = Input;
const { Title, Text } = Typography;

const defaultRequirement = (): StructuredRequirement => ({
  id: `req-${Date.now()}`,
  raw_text: 'User logs in with valid credentials; session becomes active. On logout, session ends.',
  input_fields: ['username', 'password'],
  data_ranges: [],
  conditions: ['credentials valid', 'user clicks logout'],
  expected_actions: ['authenticate user', 'show dashboard', 'clear session'],
});

function WhiteboxWorkbench() {
  const diagramId = useId().replace(/:/g, '');
  const [requirement, setRequirement] = useState<StructuredRequirement>(defaultRequirement);
  const [coverage, setCoverage] = useState<CoverageCriterion>('ALL_TRANSITIONS');
  const [model, setModel] = useState<StateMachineModel | null>(null);
  const [sequences, setSequences] = useState<TestSequence[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [mermaidText, setMermaidText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const diagramRef = useRef<HTMLDivElement>(null);

  const renderDiagram = useCallback(async () => {
    if (!diagramRef.current || !mermaidText.trim()) return;
    try {
      const { svg } = await mermaid.render(`wb-${diagramId}`, mermaidText);
      diagramRef.current.innerHTML = svg;
    } catch {
      diagramRef.current.innerHTML = '<p>Invalid Mermaid syntax</p>';
    }
  }, [diagramId, mermaidText]);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'default' });
  }, []);

  useEffect(() => {
    void renderDiagram();
  }, [renderDiagram]);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await createWhiteboxModel({
        requirement,
        coverage,
        use_llm: false,
      });
      setModel(response.model);
      setSequences(response.sequences);
      setTestCases(response.test_cases);
      setMermaidText(response.model.mermaid_diagram);
      message.success('Whitebox model generated');
    } catch (err) {
      const detail = err instanceof Error ? err.message : 'Generation failed';
      setError(detail);
      message.error(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleMermaidApply = async () => {
    if (!model) return;
    if (!model.id) {
      const regen = await regenerateMermaid({
        initial_state: model.initial_state,
        states: model.states,
        transitions: model.transitions,
      });
      setMermaidText(regen.mermaid_diagram);
      return;
    }
    setLoading(true);
    try {
      const response = await updateWhiteboxModel(model.id, {
        ...model,
        mermaid_diagram: mermaidText,
        coverage,
      });
      setModel(response.model);
      setSequences(response.sequences);
      setTestCases(response.test_cases);
      message.success('Model updated and sequences replanned');
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  const coveredItems = new Set(testCases.flatMap((tc) => tc.coverage_items));

  const caseColumns: ColumnsType<TestCase> = [
    { title: 'ID', dataIndex: 'id', width: 120 },
    { title: 'Title', dataIndex: 'title' },
    {
      title: 'Steps',
      dataIndex: 'test_steps',
      render: (steps: string[]) => steps.join(' → '),
    },
    {
      title: 'Coverage',
      dataIndex: 'coverage_items',
      render: (items: string[]) => items.map((item) => <Tag key={item}>{item}</Tag>),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>Whitebox Modeling (FR 4.0)</Title>
      {error && <Alert type="error" message={error} showIcon />}

      <Card title="Structured Requirement">
        <Form layout="vertical">
          <Form.Item label="Requirement ID">
            <Input
              value={requirement.id}
              onChange={(e) => setRequirement({ ...requirement, id: e.target.value })}
            />
          </Form.Item>
          <Form.Item label="Raw Text">
            <TextArea
              rows={3}
              value={requirement.raw_text}
              onChange={(e) => setRequirement({ ...requirement, raw_text: e.target.value })}
            />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Coverage Criterion">
                <Select<CoverageCriterion>
                  value={coverage}
                  onChange={setCoverage}
                  options={[
                    { value: 'ALL_STATES', label: 'All States' },
                    { value: 'ALL_TRANSITIONS', label: 'All Transitions' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12} style={{ display: 'flex', alignItems: 'flex-end' }}>
              <Button type="primary" loading={loading} onClick={() => void handleGenerate()}>
                Generate State Model
              </Button>
            </Col>
          </Row>
        </Form>
      </Card>

      {model && (
        <>
          <Card title="State Diagram (Mermaid)">
            <div ref={diagramRef} style={{ marginBottom: 16, overflow: 'auto' }} />
            <TextArea rows={6} value={mermaidText} onChange={(e) => setMermaidText(e.target.value)} />
            <Button style={{ marginTop: 8 }} onClick={() => void handleMermaidApply()}>
              Apply Mermaid & Replan
            </Button>
          </Card>

          <Card title="Coverage Items">
            {Array.from(coveredItems).map((item) => (
              <Tag key={item} color="blue">
                {item}
              </Tag>
            ))}
            {!coveredItems.size && <Text type="secondary">No coverage items yet</Text>}
          </Card>

          <Card title="Test Sequences">
            <Table
              rowKey="sequence_id"
              dataSource={sequences}
              pagination={false}
              columns={[
                { title: 'Sequence', dataIndex: 'sequence_id' },
                {
                  title: 'Steps',
                  dataIndex: 'steps',
                  render: (steps: string[]) => steps.join(', ') || '(initial only)',
                },
                {
                  title: 'Covered',
                  dataIndex: 'covered_items',
                  render: (items: string[]) => items.map((i) => <Tag key={i}>{i}</Tag>),
                },
              ]}
            />
          </Card>

          <Card title="Derived Test Cases">
            <Table rowKey="id" dataSource={testCases} columns={caseColumns} pagination={false} />
          </Card>
        </>
      )}
    </Space>
  );
}

export default WhiteboxWorkbench;
