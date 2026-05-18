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

/** Client type for a requirement stored in the backend. */
export interface RequirementResponse {
  id: string;
  raw_text: string;
  source_type: 'csv' | 'text' | 'form';
  input_fields: string[];
  data_ranges: string[];
  conditions: string[];
  expected_actions: string[];
  is_structured: boolean;
  risk_impact?: number | null;
  risk_likelihood?: number | null;
  risk_score?: number | null;
  priority?: string | null;
  risk_impact_rationale?: string | null;
  risk_likelihood_rationale?: string | null;
  created_at?: string;
  updated_at?: string;
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

/** Form entry for manual requirement input. */
export interface FormEntry {
  raw_text: string;
}
