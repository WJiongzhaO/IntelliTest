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
import { toStructuredRequirement } from '../utils/requirementMapper';
import { reviewOracle, synthesizeOracles, validateOracle } from '../api/oracle';

const { TextArea } = Input;
const { Title, Text } = Typography;

const sampleRequirement = (): StructuredRequirement => ({
  id: 'req-oracle-1',
  raw_text: 'User logs in with valid credentials and sees the dashboard.',
  input_fields: ['username', 'password'],
  data_ranges: [],
  conditions: ['valid credentials'],
  expected_actions: ['authenticate user', 'show dashboard'],
});

const sampleCase = (): TestCase => ({
  id: 'tc-oracle-1',
  requirement_id: 'req-oracle-1',
  title: 'Valid login path',
  precondition: 'System in LoggedOut state',
  test_steps: ['State: LoggedOut', 'State: Active'],
  test_data: 'login, valid credentials',
  technique: 'StateTransition',
  priority: 'Medium',
  coverage_items: ['LoggedOut--login-->Active'],
  modified_by_user: false,
});

function OracleEditor() {
  const [requirement, setRequirement] = useState<StructuredRequirement>(sampleRequirement);
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
      setSuiteCases(suite.test_cases);
      if (suite.test_cases[0]) {
        setTestCase(suite.test_cases[0]);
        void getRequirement(suite.test_cases[0].requirement_id).then((row) =>
          setRequirement(toStructuredRequirement(row)),
        );
      }
    } catch {
      /* ignore */
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
      message.success('Oracle synthesized');
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Synthesis failed');
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
      message.info('Validation complete');
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Validation failed');
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
      message.success(action === 'confirm' ? 'Oracle confirmed' : 'Oracle rejected');
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Review failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3}>Oracle Editor (FR 5.0)</Title>

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="Test Case">
            <Form layout="vertical">
              {suiteCases.length > 0 && (
                <Form.Item label="From combined suite">
                  <Select
                    value={testCase.id}
                    options={suiteCases.map((c) => ({
                      value: c.id,
                      label: `${c.id} (${c.technique})`,
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
              <Form.Item label="Use LLM (CoT)">
                <Switch checked={useLlm} onChange={setUseLlm} />
              </Form.Item>
              <Form.Item label="Title">
                <Input
                  value={testCase.title}
                  onChange={(e) => setTestCase({ ...testCase, title: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="Precondition">
                <Input
                  value={testCase.precondition}
                  onChange={(e) => setTestCase({ ...testCase, precondition: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="Test Steps (one per line)">
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
              <Form.Item label="Test Data">
                <Input
                  value={testCase.test_data}
                  onChange={(e) => setTestCase({ ...testCase, test_data: e.target.value })}
                />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="CoT Reasoning & Expected Result">
            {oracle && !oracle.consistent_with_requirement && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 12 }}
                message="Consistency issues"
                description={
                  <List
                    size="small"
                    dataSource={oracle.validation_messages}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                }
              />
            )}

            <Text strong>Reasoning steps</Text>
            <List
              size="small"
              style={{ marginBottom: 12 }}
              dataSource={oracle?.reasoning_steps ?? []}
              locale={{ emptyText: 'Run synthesis to generate CoT steps' }}
              renderItem={(item, index) => (
                <List.Item>
                  {index + 1}. {item}
                </List.Item>
              )}
            />

            <Form.Item label="Expected Result">
              <TextArea
                rows={4}
                value={expectedEdit}
                onChange={(e) => setExpectedEdit(e.target.value)}
              />
            </Form.Item>

            {oracle && (
              <Space wrap>
                <Tag color={oracle.consistent_with_requirement ? 'green' : 'orange'}>
                  {oracle.consistent_with_requirement ? 'Consistent' : 'Review needed'}
                </Tag>
                <Tag>{oracle.status}</Tag>
                {oracle.modified_by_user && <Tag color="blue">User modified</Tag>}
              </Space>
            )}
          </Card>
        </Col>
      </Row>

      <Card>
        <Space wrap>
          <Button type="primary" loading={loading} onClick={() => void handleSynthesize()}>
            Synthesize Oracle
          </Button>
          <Button loading={loading} onClick={() => void handleValidate()}>
            Validate Only
          </Button>
          <Button loading={loading} disabled={!oracle} onClick={() => void handleReview('confirm')}>
            Confirm
          </Button>
          <Button danger loading={loading} disabled={!oracle} onClick={() => void handleReview('reject')}>
            Reject
          </Button>
        </Space>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">
            Requirement raw text can be edited for member E integration — id: {requirement.id}
          </Text>
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
