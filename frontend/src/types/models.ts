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

/** ISO 29119-4 black-box testing techniques. */
export type BlackBoxTechnique = 'EP' | 'BVA' | 'DT';

/** Coverage item for test design traceability. */
export interface CoverageItem {
  id: string;
  requirement_id: string;
  description: string;
  item_type: string;
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

/** Form entry for manual requirement input. */
export interface FormEntry {
  raw_text: string;
}

/** Coverage report structure (FR 3.0). */
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

/** Whitebox coverage criterion (FR 4.0). */
export type CoverageCriterion = 'ALL_STATES' | 'ALL_TRANSITIONS';

/** Five-tuple state transition edge. */
export interface StateTransitionTuple {
  state: string;
  event: string;
  guard?: string;
  action?: string;
  next_state: string;
}

/** State machine model with Mermaid diagram. */
export interface StateMachineModel {
  initial_state: string;
  states: string[];
  transitions: StateTransitionTuple[];
  mermaid_diagram: string;
  id?: string;
  requirement_id?: string;
  revision?: number;
}

/** Planned test sequence for state coverage. */
export interface TestSequence {
  sequence_id: string;
  steps: string[];
  covered_items: string[];
  derived_test_cases: TestCase[];
}

/** Oracle synthesis / review record (FR 5.0). */
export type OracleStatus = 'pending_review' | 'confirmed' | 'rejected';

export interface OracleResult {
  id: string;
  test_case_id: string;
  expected_result: string;
  reasoning_steps: string[];
  confidence?: number;
  consistent_with_requirement: boolean;
  validation_messages: string[];
  status: OracleStatus;
  modified_by_user: boolean;
  revision?: number;
}
