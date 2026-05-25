import { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  List,
  Row,
  Select,
  Space,
  Switch,
  Tag,
  Typography,
  message,
} from 'antd';
import { getRequirement } from '../api/requirements';
import { SUITE_STORAGE_KEY } from './TestDesignWorkbench';
import type { OracleResult, StructuredRequirement, TestCase, TestSuite } from '../types/models';
import { saveSuiteForReviewExport } from '../utils/exportSuiteStorage';
import { getRequirementDisplayName, toStructuredRequirement } from '../utils/requirementMapper';
import { reviewOracle, synthesizeOracles, validateOracle } from '../api/oracle';

const { TextArea } = Input;
const { Title, Text } = Typography;

const statusLabels: Record<string, string> = {
  pending_review: '待审查',
  confirmed: '已确认',
  rejected: '已拒绝',
};

const sampleRequirement = (): StructuredRequirement => ({
  id: 'req-oracle-1',
  title: '登录认证需求',
  raw_text: '用户使用有效账号密码登录后可以看到系统首页。',
  input_fields: ['用户名', '密码'],
  data_ranges: [],
  conditions: ['账号密码有效'],
  expected_actions: ['认证用户', '展示系统首页'],
});

const sampleCase = (): TestCase => ({
  id: 'tc-oracle-1',
  requirement_id: 'req-oracle-1',
  title: '有效登录路径',
  precondition: '系统处于未登录状态',
  test_steps: ['状态：未登录', '状态：已登录'],
  test_data: '登录，有效账号密码',
  technique: 'StateTransition',
  priority: 'Medium',
  coverage_items: ['LoggedOut--login-->Active'],
  modified_by_user: false,
});

function OracleEditor() {
  const [requirement, setRequirement] = useState<StructuredRequirement>(sampleRequirement);
  const [suite, setSuite] = useState<TestSuite | null>(null);
  const [suiteCases, setSuiteCases] = useState<TestCase[]>([]);
  const [testCase, setTestCase] = useState<TestCase>(sampleCase);
  const [oracle, setOracle] = useState<OracleResult | null>(null);
  const [expectedEdit, setExpectedEdit] = useState('');
  const [loading, setLoading] = useState(false);
  const [useLlm, setUseLlm] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem(SUITE_STORAGE_KEY);
    if (!raw) return;
    try {
      const suite = JSON.parse(raw) as TestSuite;
      setSuite(suite);
      setSuiteCases(suite.test_cases);
      if (suite.test_cases[0]) {
        setTestCase(suite.test_cases[0]);
        void getRequirement(suite.test_cases[0].requirement_id).then((row) =>
          setRequirement(toStructuredRequirement(row)),
        );
      }
    } catch {
      /* 忽略无效的会话数据 */
    }
  }, []);

  const handleSynthesize = async () => {
    setLoading(true);
    try {
      const { oracles } = await synthesizeOracles({
        requirement,
        test_cases: [testCase],
        use_llm: useLlm,
      });
      const first = oracles[0] ?? null;
      setOracle(first);
      setExpectedEdit(first?.expected_result ?? '');
      message.success('测试预言已生成');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '生成失败');
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!expectedEdit) return;
    setLoading(true);
    try {
      const result = await validateOracle({
        requirement,
        test_case: testCase,
        expected_result: expectedEdit,
      });
      setOracle(result);
      message.info('校验完成');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '校验失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (action: 'confirm' | 'reject') => {
    if (!oracle) return;
    setLoading(true);
    try {
      const updated = await reviewOracle(oracle.id, {
        action,
        edited_expected_result: action === 'confirm' ? expectedEdit : undefined,
        sync_test_case: true,
      });
      setOracle(updated);
      message.success(action === 'confirm' ? '测试预言已确认' : '测试预言已拒绝');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '审查失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUseForExport = () => {
    if (!suite) {
      message.warning('当前没有可覆盖到审查导出的测试套件');
      return;
    }

    const nextCase: TestCase = {
      ...testCase,
      expected_result: expectedEdit,
      modified_by_user: true,
    };
    const nextCases = suiteCases.map((item) => (item.id === nextCase.id ? nextCase : item));
    const nextSuite = { ...suite, test_cases: nextCases };

    setTestCase(nextCase);
    setSuiteCases(nextCases);
    setSuite(nextSuite);
    saveSuiteForReviewExport(nextSuite);
    message.success('已将当前测试预言结果设为审查导出内容');
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>测试预言编辑</Title>

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="测试用例">
            <Form layout="vertical">
              {suiteCases.length > 0 && (
                <Form.Item label="从测试套件选择">
                  <Select
                    value={testCase.id}
                    options={suiteCases.map((c) => ({
                      value: c.id,
                      label: `${c.id}（${c.technique}）`,
                    }))}
                    onChange={(id) => {
                      const picked = suiteCases.find((c) => c.id === id);
                      if (picked) {
                        setTestCase(picked);
                        setExpectedEdit(picked.expected_result ?? '');
                      }
                    }}
                  />
                </Form.Item>
              )}
              <Form.Item label="使用大模型推理">
                <Switch checked={useLlm} onChange={setUseLlm} />
              </Form.Item>
              <Form.Item label="标题">
                <Input
                  value={testCase.title}
                  onChange={(e) => setTestCase({ ...testCase, title: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="前置条件">
                <Input
                  value={testCase.precondition}
                  onChange={(e) => setTestCase({ ...testCase, precondition: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="测试步骤（每行一步）">
                <TextArea
                  rows={4}
                  value={testCase.test_steps.join('\n')}
                  onChange={(e) =>
                    setTestCase({
                      ...testCase,
                      test_steps: e.target.value.split('\n').filter(Boolean),
                    })
                  }
                />
              </Form.Item>
              <Form.Item label="测试数据">
                <Input
                  value={testCase.test_data}
                  onChange={(e) => setTestCase({ ...testCase, test_data: e.target.value })}
                />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="推理过程与预期结果">
            {oracle && !oracle.consistent_with_requirement && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 12 }}
                message="一致性问题"
                description={
                  <List
                    size="small"
                    dataSource={oracle.validation_messages}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                }
              />
            )}

            <Text strong>推理步骤</Text>
            <List
              size="small"
              style={{ marginBottom: 12 }}
              dataSource={oracle?.reasoning_steps ?? []}
              locale={{ emptyText: '请先生成测试预言' }}
              renderItem={(item, index) => (
                <List.Item>
                  {index + 1}. {item}
                </List.Item>
              )}
            />

            <Form.Item label="预期结果">
              <TextArea
                rows={4}
                value={expectedEdit}
                onChange={(e) => setExpectedEdit(e.target.value)}
              />
            </Form.Item>

            {oracle && (
              <Space wrap>
                <Tag color={oracle.consistent_with_requirement ? 'green' : 'orange'}>
                  {oracle.consistent_with_requirement ? '一致' : '需要审查'}
                </Tag>
                <Tag>{statusLabels[oracle.status] ?? oracle.status}</Tag>
                {oracle.modified_by_user && <Tag color="blue">已人工修改</Tag>}
              </Space>
            )}
          </Card>
        </Col>
      </Row>

      <Card>
        <Space wrap>
          <Button type="primary" loading={loading} onClick={() => void handleSynthesize()}>
            生成测试预言
          </Button>
          <Button loading={loading} onClick={() => void handleValidate()}>
            仅校验
          </Button>
          <Button loading={loading} disabled={!oracle} onClick={() => void handleReview('confirm')}>
            确认
          </Button>
          <Button danger loading={loading} disabled={!oracle} onClick={() => void handleReview('reject')}>
            拒绝
          </Button>
          <Button disabled={!suite} onClick={handleUseForExport}>
            覆盖审查导出内容
          </Button>
        </Space>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">需求原文：{getRequirementDisplayName(requirement)}</Text>
          <TextArea
            style={{ marginTop: 8 }}
            rows={2}
            value={requirement.raw_text}
            onChange={(e) => setRequirement({ ...requirement, raw_text: e.target.value })}
          />
        </div>
      </Card>
    </Space>
  );
}

export default OracleEditor;
