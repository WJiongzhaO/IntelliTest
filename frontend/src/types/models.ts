/** Client type for a parsed/structured requirement. */
export interface StructuredRequirement {
  id: string;
  raw_text: string;
  input_fields: string[];
  data_ranges: string[];
  conditions: string[];
  expected_actions: string[];
  risk_score?: number;
  priority?: string;
}

/** ISO 29119-4 aligned test case type. */
export interface TestCase {
  id: string;
  requirement_id: string;
  title: string;
  precondition?: string;
  test_steps: string[];
  test_data?: string;
  expected_result?: string;
  technique?: 'EP' | 'BVA' | 'DT' | 'StateTransition';
  priority: 'High' | 'Medium' | 'Low';
  risk_score?: number;
  coverage_items: string[];
  modified_by_user: boolean;
}

/** A named collection of test cases. */
export interface TestSuite {
  id: string;
  name: string;
  description?: string;
  test_cases: TestCase[];
  created_at?: string;
  optimization_applied?: string;
}
