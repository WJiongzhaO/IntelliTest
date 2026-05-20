import apiClient from './client';
import type {
  BlackBoxGenerationResult,
  BlackBoxTechnique,
  CoverageItem,
  StructuredRequirement,
  TechniqueInfo,
  TestCase,
} from '../types/models';

export async function getBlackboxTechniques(): Promise<Record<string, TechniqueInfo>> {
  const { data } = await apiClient.get<Record<string, TechniqueInfo>>('/blackbox/techniques');
  return data;
}

export async function generateAllBlackbox(
  requirement: StructuredRequirement,
): Promise<TestCase[]> {
  const { data } = await apiClient.post<TestCase[]>('/blackbox/generate/all', requirement);
  return data;
}

export async function generateBlackboxTechnique(
  requirement: StructuredRequirement,
  technique: BlackBoxTechnique,
): Promise<TestCase[]> {
  const { data } = await apiClient.post<TestCase[]>(
    `/blackbox/generate/${technique}`,
    requirement,
  );
  return data;
}

export async function generateBlackboxWithCoverage(
  requirement: StructuredRequirement,
  selectedTechniques?: BlackBoxTechnique[],
): Promise<BlackBoxGenerationResult> {
  const { data } = await apiClient.post<BlackBoxGenerationResult>(
    '/blackbox/generate/with-coverage',
    {
      requirement,
      selected_techniques: selectedTechniques,
    },
  );
  return data;
}

export async function identifyCoverageItems(
  requirement: StructuredRequirement,
): Promise<CoverageItem[]> {
  const { data } = await apiClient.post<CoverageItem[]>(
    '/blackbox/coverage/identify',
    requirement,
  );
  return data;
}
