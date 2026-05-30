import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  Popconfirm,
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
import { regenerateMermaid, updateWhiteboxModel } from '../api/whitebox';
import StructuredRequirementTable from '../components/StructuredRequirementTable';
import { useTestDesignJobStore } from '../stores/testDesignJobStore';
import { getRequirementDisplayName, toStructuredRequirement } from '../utils/requirementMapper';
import type { RequirementResponse } from '../types/models';
import mermaid from 'mermaid';
import type { ColumnsType } from 'antd/es/table';
import type { CoverageCriterion, TestCase } from '../types/models';

const { TextArea } = Input;
const { Title, Text } = Typography;

function WhiteboxWorkbench() {
  const diagramId = useId().replace(/:/g, '');
  const [requirements, setRequirements] = useState<RequirementResponse[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [useLlm, setUseLlm] = useState(false);
  const [coverage, setCoverage] = useState<CoverageCriterion>('ALL_TRANSITIONS');
  const [viewRequirementId, setViewRequirementId] = useState<string>();
  const [mermaidText, setMermaidText] = useState('');
  const [diagramLoading, setDiagramLoading] = useState(false);
  const diagramRef = useRef<HTMLDivElement>(null);

  const { whiteboxResults, enqueueWhitebox } = useTestDesignJobStore();

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
    setListLoading(true);
    void listRequirements()
      .then((rows) => setRequirements(rows.filter((r) => r.is_structured)))
      .catch(() => message.error('需求列表加载失败'))
      .finally(() => setListLoading(false));
  }, []);

  useEffect(() => {
    void renderDiagram();
  }, [renderDiagram]);

  const selectedRecords = useMemo(
    () => requirements.filter((r) => selectedRowKeys.includes(r.id)),
    [requirements, selectedRowKeys],
  );

  const completedIds = Object.keys(whiteboxResults);
  const completedRows = requirements.filter((r) => completedIds.includes(r.id));

  const activeResult = useMemo(() => {
    if (!viewRequirementId) return completedIds.length > 0 ? whiteboxResults[completedIds[0]] : null;
    return whiteboxResults[viewRequirementId] ?? null;
  }, [whiteboxResults, viewRequirementId, completedIds]);

  useEffect(() => {
    if (activeResult?.model.mermaid_diagram) {
      setMermaidText(activeResult.model.mermaid_diagram);
    }
  }, [activeResult]);

  useEffect(() => {
    if (completedIds.length > 0 && !viewRequirementId) {
      setViewRequirementId(completedIds[0]);
    }
  }, [completedIds, viewRequirementId]);

  const handleGenerate = (records = selectedRecords) => {
    if (records.length === 0) {
      message.warning('请至少选择一条已结构化需求');
      return;
    }

    enqueueWhitebox(
      records.map((row) => ({
        internalId: row.id,
        requirement: toStructuredRequirement(row),
        title: getRequirementDisplayName(row),
      })),
      { coverage, useLlm },
    );
    message.success(`已将 ${records.length} 条需求加入白盒建模队列`);
  };

  const handleMermaidApply = async () => {
    if (!activeResult?.model) return;

    const model = activeResult.model;
    if (!model.id) {
      const regen = await regenerateMermaid({
        initial_state: model.initial_state,
        states: model.states,
        transitions: model.transitions,
      });
      setMermaidText(regen.mermaid_diagram);
      return;
    }

    setDiagramLoading(true);
    try {
      const response = await updateWhiteboxModel(model.id, {
        ...model,
        mermaid_diagram: mermaidText,
        coverage,
      });
      const reqId = viewRequirementId ?? model.requirement_id;
      if (!reqId) return;
      useTestDesignJobStore.setState((state) => ({
        whiteboxResults: {
          ...state.whiteboxResults,
          [reqId]: response,
        },
      }));
      message.success('模型已更新，覆盖序列已重新规划');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '更新失败');
    } finally {
      setDiagramLoading(false);
    }
  };

  const testCases = activeResult?.test_cases ?? [];
  const sequences = activeResult?.sequences ?? [];
  const model = activeResult?.model ?? null;
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

  const resultSummaryColumns: ColumnsType<RequirementResponse> = [
    {
      title: '需求',
      key: 'title',
      render: (_: unknown, record) => getRequirementDisplayName(record),
    },
    {
      title: '状态数',
      key: 'states',
      width: 90,
      render: (_: unknown, record) => whiteboxResults[record.id]?.model.states.length ?? '-',
    },
    {
      title: '用例数',
      key: 'cases',
      width: 90,
      render: (_: unknown, record) => whiteboxResults[record.id]?.test_cases.length ?? '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record) => (
        <Button
          type="link"
          size="small"
          disabled={!whiteboxResults[record.id]}
          onClick={() => setViewRequirementId(record.id)}
        >
          查看
        </Button>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>白盒建模</Title>

      <Alert
        showIcon
        type="info"
        message="在下方表格勾选需求，可单条或批量生成状态模型；任务在后台队列中执行，生成完成后在结果区查看详情。"
      />

      <Card
        title="选择需求"
        extra={
          <Popconfirm
            title={`为选中的 ${selectedRecords.length} 条需求生成白盒模型？`}
            onConfirm={() => handleGenerate()}
            okText="确认"
            cancelText="取消"
            disabled={selectedRecords.length === 0}
          >
            <Button type="primary" disabled={selectedRecords.length === 0}>
              {selectedRecords.length > 1
                ? `批量生成 (${selectedRecords.length})`
                : '生成状态模型'}
            </Button>
          </Popconfirm>
        }
      >
        <Form layout="vertical">
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
            <Col span={12}>
              <Form.Item label="使用大模型抽取">
                <Switch checked={useLlm} onChange={setUseLlm} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
        <StructuredRequirementTable
          requirements={requirements}
          loading={listLoading}
          selectedRowKeys={selectedRowKeys}
          onSelectionChange={setSelectedRowKeys}
        />
      </Card>

      {completedRows.length > 0 && (
        <Card title="生成结果">
          <Table<RequirementResponse>
            rowKey="id"
            size="small"
            dataSource={completedRows}
            columns={resultSummaryColumns}
            pagination={false}
            style={{ marginBottom: 16 }}
          />
        </Card>
      )}

      {model && (
        <>
          <Card
            title={
              viewRequirementId
                ? `状态图 · ${getRequirementDisplayName(requirements.find((r) => r.id === viewRequirementId)!)}`
                : '状态图（Mermaid）'
            }
          >
            <div ref={diagramRef} style={{ marginBottom: 16, overflow: 'auto' }} />
            <TextArea rows={6} value={mermaidText} onChange={(e) => setMermaidText(e.target.value)} />
            <Button
              style={{ marginTop: 8 }}
              loading={diagramLoading}
              onClick={() => void handleMermaidApply()}
            >
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
