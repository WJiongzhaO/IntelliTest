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
  useLlm = true,
): Promise<TestCase[]> {
  const { data } = await apiClient.post<TestCase[]>('/blackbox/generate/all', {
    requirement,
    use_llm: useLlm,
  });
  return data;
}

export async function generateBlackboxTechnique(
  requirement: StructuredRequirement,
  technique: BlackBoxTechnique,
  useLlm = true,
): Promise<TestCase[]> {
  const { data } = await apiClient.post<TestCase[]>(
    `/blackbox/generate/${technique}`,
    { requirement, use_llm: useLlm },
  );
  return data;
}

export async function generateBlackboxWithCoverage(
  requirement: StructuredRequirement,
  selectedTechniques?: BlackBoxTechnique[],
  requirementId?: string,
  useLlm = true,
): Promise<BlackBoxGenerationResult> {
  const { data } = await apiClient.post<BlackBoxGenerationResult>(
    '/blackbox/generate/with-coverage',
    {
      requirement,
      selected_techniques: selectedTechniques,
      requirement_id: requirementId,
      use_llm: useLlm,
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
