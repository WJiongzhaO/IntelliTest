import { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Empty,
  Form,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { generateBlackboxWithCoverage } from '../api/blackbox';
import { listRequirements } from '../api/requirements';
import { SUITE_STORAGE_KEY } from './TestDesignWorkbench';
import type {
  BlackBoxGenerationResult,
  BlackBoxTechnique,
  CoverageItem,
  RequirementResponse,
  TestCase,
  TestSuite,
} from '../types/models';
import { toStructuredRequirement } from '../utils/requirementMapper';

const { Title, Text } = Typography;

const techniqueOptions = [
  { label: '等价类划分（EP）', value: 'EP' },
  { label: '边界值分析（BVA）', value: 'BVA' },
  { label: '判定表（DT）', value: 'DT' },
];

function buildSuite(requirementId: string, result: BlackBoxGenerationResult): TestSuite {
  return {
    id: `blackbox-${Date.now()}`,
    name: '黑盒测试套件',
    description: '由黑盒测试工作台生成',
    test_cases: result.test_cases.map((testCase) => ({
      ...testCase,
      requirement_id: testCase.requirement_id || requirementId,
      modified_by_user: testCase.modified_by_user ?? false,
    })),
    created_at: new Date().toISOString(),
  };
}

export default function BlackboxWorkbench() {
  const [requirements, setRequirements] = useState<RequirementResponse[]>([]);
  const [selectedId, setSelectedId] = useState<string>();
  const [techniques, setTechniques] = useState<BlackBoxTechnique[]>(['EP', 'BVA', 'DT']);
  const [result, setResult] = useState<BlackBoxGenerationResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void listRequirements()
      .then((rows) => {
        const structured = rows.filter((item) => item.is_structured);
        setRequirements(structured);
        setSelectedId((current) => current ?? structured[0]?.id);
      })
      .catch(() => message.error('需求列表加载失败，请先检查后端服务'));
  }, []);

  const handleGenerate = async () => {
    const row = requirements.find((item) => item.id === selectedId);
    if (!row) {
      message.warning('请选择一条已结构化需求');
      return;
    }

    setLoading(true);
    try {
      const generated = await generateBlackboxWithCoverage(toStructuredRequirement(row), techniques);
      setResult(generated);
      sessionStorage.setItem(SUITE_STORAGE_KEY, JSON.stringify(buildSuite(row.id, generated)));
      message.success(`已生成 ${generated.test_cases.length} 条黑盒测试用例`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '黑盒用例生成失败');
    } finally {
      setLoading(false);
    }
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
        message="请先在需求输入页完成结构化，再回到这里选择需求并生成黑盒测试用例。"
      />

      <Card title="生成配置">
        <Form layout="vertical">
          <Form.Item label="已结构化需求">
            <Select
              value={selectedId}
              onChange={setSelectedId}
              placeholder="选择需求"
              options={requirements.map((item) => ({
                value: item.id,
                label: `${item.id}（风险=${item.risk_score ?? '-'}）`,
              }))}
            />
          </Form.Item>
          <Form.Item label="黑盒测试方法">
            <Checkbox.Group
              options={techniqueOptions}
              value={techniques}
              onChange={(value) => setTechniques(value as BlackBoxTechnique[])}
            />
          </Form.Item>
          <Button
            type="primary"
            loading={loading}
            disabled={!selectedId || techniques.length === 0}
            onClick={() => void handleGenerate()}
          >
            生成黑盒用例
          </Button>
        </Form>
      </Card>

      {result ? (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={12} lg={6}>
              <div className="tool-panel">
                <Statistic title="覆盖项总数" value={result.coverage_report.total_coverage_items} />
              </div>
            </Col>
            <Col xs={12} lg={6}>
              <div className="tool-panel">
                <Statistic title="已覆盖" value={result.coverage_report.covered_items} />
              </div>
            </Col>
            <Col xs={12} lg={6}>
              <div className="tool-panel">
                <Statistic title="未覆盖" value={result.coverage_report.uncovered_items} />
              </div>
            </Col>
            <Col xs={12} lg={6}>
              <div className="tool-panel">
                <Statistic
                  title="覆盖率"
                  suffix="%"
                  precision={1}
                  value={result.coverage_report.coverage_percentage}
                />
              </div>
            </Col>
          </Row>

          <Card title="黑盒测试用例">
            <Table<TestCase>
              rowKey="id"
              dataSource={result.test_cases}
              columns={caseColumns}
              pagination={{ pageSize: 8 }}
            />
          </Card>

          <Card title="覆盖项追踪">
            <Table<CoverageItem>
              rowKey="id"
              dataSource={result.coverage_items}
              columns={coverageColumns}
              pagination={{ pageSize: 8 }}
            />
          </Card>
        </>
      ) : (
        <div className="tool-panel">
          <Empty description="暂无黑盒测试结果" />
        </div>
      )}
    </Space>
  );
}
