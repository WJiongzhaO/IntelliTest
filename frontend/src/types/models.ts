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

/** ISO 29119-4 black-box testing techniques. */
export type BlackBoxTechnique = 'EP' | 'BVA' | 'DT';

/** Coverage item for test design traceability. */
export interface CoverageItem {
  id: string;
  requirement_id: string;
  description: string;
  item_type: string; // input_field, boundary, condition, decision_rule, etc.
  selected_techniques: BlackBoxTechnique[];
  covered_by_test_cases: string[];
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
  technique?: BlackBoxTechnique | 'StateTransition';
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

/** Coverage report structure. */
export interface CoverageReport {
  total_coverage_items: number;
  covered_items: number;
  uncovered_items: number;
  coverage_percentage: number;
  type_distribution: Record<string, { total: number; covered: number }>;
  technique_usage: Record<string, number>;
  uncovered_item_details: Array<{
    id: string;
    description: string;
    type: string;
  }>;
}

/** Black-box generation result with coverage tracking. */
export interface BlackBoxGenerationResult {
  coverage_items: CoverageItem[];
  test_cases: TestCase[];
  coverage_report: CoverageReport;
}

/** Information about a testing technique. */
export interface TechniqueInfo {
  name: string;
  description: string;
  standard: string;
  best_for: string;
}
