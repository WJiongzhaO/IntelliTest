import apiClient from './client';
import type { CoverageItem, RequirementResponse, TestCase, TestSuite } from '../types';

export interface RequirementReviewBundle {
  requirement_id: string;
  external_id?: string | null;
  title?: string | null;
  requirement_ref: string;
  suite?: TestSuite | null;
  test_cases: TestCase[];
  coverage_items: CoverageItem[];
}

export interface ReviewArtifactsResponse {
  bundles: RequirementReviewBundle[];
}

export async function getReviewArtifacts(): Promise<ReviewArtifactsResponse> {
  const { data } = await apiClient.get<ReviewArtifactsResponse>('/artifacts/review');
  return data;
}

export async function saveReviewBundle(
  requirementId: string,
  testCases: TestCase[],
  coverageItems: CoverageItem[],
): Promise<void> {
  await apiClient.put(`/artifacts/review/${requirementId}`, {
    requirement_id: requirementId,
    test_cases: testCases,
    coverage_items: coverageItems,
  });
}
