import apiClient from './client';
import type {
  CoverageCriterion,
  StructuredRequirement,
  TestCase,
  TestSuite,
} from '../types/models';

export interface CombinedDesignRequest {
  requirement_id?: string;
  requirement?: StructuredRequirement;
  techniques: string[];
  coverage: CoverageCriterion;
  synthesize_oracles?: boolean;
  use_llm?: boolean;
  blackbox_cases?: TestCase[];
}

export async function runCombinedDesign(body: CombinedDesignRequest): Promise<TestSuite> {
  const { data } = await apiClient.post<TestSuite>('/test-design/combined', body);
  return data;
}
