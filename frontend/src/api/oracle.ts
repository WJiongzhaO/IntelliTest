import apiClient from './client';
import type {
  OracleResult,
  StructuredRequirement,
  TestCase,
  TestSuite,
} from '../types/models';

export interface OracleSynthesizeRequest {
  requirement: StructuredRequirement;
  test_cases: TestCase[];
  use_llm?: boolean;
}

export interface OracleReviewRequest {
  action: 'confirm' | 'reject';
  edited_expected_result?: string;
  sync_test_case?: boolean;
}

export async function synthesizeOracles(
  body: OracleSynthesizeRequest,
): Promise<{ oracles: OracleResult[] }> {
  const { data } = await apiClient.post<{ oracles: OracleResult[] }>('/oracle/synthesize', body);
  return data;
}

export async function validateOracle(body: {
  requirement: StructuredRequirement;
  test_case: TestCase;
  expected_result: string;
}): Promise<OracleResult> {
  const { data } = await apiClient.post<OracleResult>('/oracle/validate', body);
  return data;
}

export async function reviewOracle(
  oracleId: string,
  body: OracleReviewRequest,
): Promise<OracleResult> {
  const { data } = await apiClient.put<OracleResult>(`/oracle/${oracleId}/review`, body);
  return data;
}

export async function batchOraclesFromSuite(body: {
  requirement: StructuredRequirement;
  suite: TestSuite;
  use_llm?: boolean;
}): Promise<{ oracles: OracleResult[] }> {
  const { data } = await apiClient.post<{ oracles: OracleResult[] }>(
    '/oracle/batch-from-suite',
    body,
  );
  return data;
}
