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
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { listRequirements } from '../api/requirements';
import { toStructuredRequirement } from '../utils/requirementMapper';
import type { RequirementResponse } from '../types/models';
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
  raw_text: '用户使用有效账号密码登录后进入系统；用户退出登录后会话结束。',
  input_fields: ['用户名', '密码'],
  data_ranges: [],
  conditions: ['账号密码有效', '用户点击退出登录'],
  expected_actions: ['认证用户', '展示系统首页', '清除会话'],
});

function WhiteboxWorkbench() {
  const diagramId = useId().replace(/:/g, '');
  const [dbRows, setDbRows] = useState<RequirementResponse[]>([]);
  const [requirement, setRequirement] = useState<StructuredRequirement>(defaultRequirement);
  const [useLlm, setUseLlm] = useState(false);
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
      diagramRef.current.innerHTML = '<p>Mermaid 语法无效</p>';
    }
  }, [diagramId, mermaidText]);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'default' });
  }, []);

  useEffect(() => {
    void listRequirements()
      .then((rows) => setDbRows(rows.filter((r) => r.is_structured)))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    void renderDiagram();
  }, [renderDiagram]);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await createWhiteboxModel({
        requirement_id: requirement.id,
        requirement,
        coverage,
        use_llm: useLlm,
      });
      setModel(response.model);
      setSequences(response.sequences);
      setTestCases(response.test_cases);
      setMermaidText(response.model.mermaid_diagram);
      message.success('白盒状态模型已生成');
    } catch (err) {
      const detail = err instanceof Error ? err.message : '生成失败';
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
      message.success('模型已更新，覆盖序列已重新规划');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '更新失败');
    } finally {
      setLoading(false);
    }
  };

  const coveredItems = new Set(testCases.flatMap((tc) => tc.coverage_items));

  const caseColumns: ColumnsType<TestCase> = [
    { title: '编号', dataIndex: 'id', width: 120 },
    { title: '标题', dataIndex: 'title' },
    {
      title: '步骤',
      dataIndex: 'test_steps',
      render: (steps: string[]) => steps.join(' → '),
    },
    {
      title: '覆盖项',
      dataIndex: 'coverage_items',
      render: (items: string[]) => items.map((item) => <Tag key={item}>{item}</Tag>),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>白盒建模</Title>
      {error && <Alert type="error" message={error} showIcon />}

      <Card title="结构化需求">
        <Form layout="vertical">
          <Form.Item label="从需求列表加载">
            <Select
              allowClear
              placeholder="选择已结构化需求"
              options={dbRows.map((r) => ({ value: r.id, label: r.id }))}
              onChange={(id) => {
                const row = dbRows.find((r) => r.id === id);
                if (row) setRequirement(toStructuredRequirement(row));
              }}
            />
          </Form.Item>
          <Form.Item label="使用大模型抽取">
            <Switch checked={useLlm} onChange={setUseLlm} />
          </Form.Item>
          <Form.Item label="需求编号">
            <Input
              value={requirement.id}
              onChange={(e) => setRequirement({ ...requirement, id: e.target.value })}
            />
          </Form.Item>
          <Form.Item label="需求原文">
            <TextArea
              rows={3}
              value={requirement.raw_text}
              onChange={(e) => setRequirement({ ...requirement, raw_text: e.target.value })}
            />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="覆盖准则">
                <Select<CoverageCriterion>
                  value={coverage}
                  onChange={setCoverage}
                  options={[
                    { value: 'ALL_STATES', label: '全部状态' },
                    { value: 'ALL_TRANSITIONS', label: '全部转换' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12} style={{ display: 'flex', alignItems: 'flex-end' }}>
              <Button type="primary" loading={loading} onClick={() => void handleGenerate()}>
                生成状态模型
              </Button>
            </Col>
          </Row>
        </Form>
      </Card>

      {model && (
        <>
          <Card title="状态图（Mermaid）">
            <div ref={diagramRef} style={{ marginBottom: 16, overflow: 'auto' }} />
            <TextArea rows={6} value={mermaidText} onChange={(e) => setMermaidText(e.target.value)} />
            <Button style={{ marginTop: 8 }} onClick={() => void handleMermaidApply()}>
              应用图并重新规划
            </Button>
          </Card>

          <Card title="覆盖项">
            {Array.from(coveredItems).map((item) => (
              <Tag key={item} color="blue">
                {item}
              </Tag>
            ))}
            {!coveredItems.size && <Text type="secondary">暂无覆盖项</Text>}
          </Card>

          <Card title="测试序列">
            <Table
              rowKey="sequence_id"
              dataSource={sequences}
              pagination={false}
              columns={[
                { title: '序列', dataIndex: 'sequence_id' },
                {
                  title: '步骤',
                  dataIndex: 'steps',
                  render: (steps: string[]) => steps.join(', ') || '仅初始状态',
                },
                {
                  title: '已覆盖',
                  dataIndex: 'covered_items',
                  render: (items: string[]) => items.map((i) => <Tag key={i}>{i}</Tag>),
                },
              ]}
            />
          </Card>

          <Card title="派生测试用例">
            <Table rowKey="id" dataSource={testCases} columns={caseColumns} pagination={false} />
          </Card>
        </>
      )}
    </Space>
  );
}

export default WhiteboxWorkbench;
