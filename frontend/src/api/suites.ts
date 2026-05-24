import apiClient from './client';
import type { OptimizationStrategy, OptimizeSuiteResponse, TestCase } from '../types/models';

export async function optimizeSuite(
  testCases: TestCase[],
  strategy: OptimizationStrategy,
  coverageUniverse?: string[],
): Promise<OptimizeSuiteResponse> {
  const { data } = await apiClient.post<OptimizeSuiteResponse>('/suites/optimize', {
    test_cases: testCases,
    strategy,
    coverage_universe: coverageUniverse,
  });
  return data;
}
