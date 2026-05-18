import apiClient from './client';
import type {
  StructuredRequirement,
  TestCase,
  CoverageItem,
  BlackBoxGenerationResult,
  TechniqueInfo,
} from '../types/models';

/**
 * Black-box testing API functions
 */

/**
 * Get information about available black-box testing techniques
 */
export const getTechniques = (): Promise<{ data: Record<string, TechniqueInfo> }> => {
  return apiClient.get('/blackbox/techniques');
};

/**
 * Generate test cases using all three black-box techniques (EP, BVA, DT)
 */
export const generateAllTechniques = (
  requirement: StructuredRequirement
): Promise<{ data: TestCase[] }> => {
  return apiClient.post('/blackbox/generate/all', requirement);
};

/**
 * Generate test cases using a specific technique
 */
export const generateSpecificTechnique = (
  requirement: StructuredRequirement,
  technique: 'EP' | 'BVA' | 'DT'
): Promise<{ data: TestCase[] }> => {
  return apiClient.post(`/blackbox/generate/${technique}`, requirement);
};

/**
 * Generate test cases with full coverage tracking and reporting
 */
export const generateWithCoverage = (
  requirement: StructuredRequirement,
  selectedTechniques?: ('EP' | 'BVA' | 'DT')[]
): Promise<{ data: BlackBoxGenerationResult }> => {
  return apiClient.post('/blackbox/generate/with-coverage', {
    requirement,
    selected_techniques: selectedTechniques,
  });
};

/**
 * Identify coverage items from a structured requirement
 */
export const identifyCoverageItems = (
  requirement: StructuredRequirement
): Promise<{ data: CoverageItem[] }> => {
  return apiClient.post('/blackbox/coverage/identify', requirement);
};

/**
 * Select testing techniques for a specific coverage item
 */
export const selectTechniquesForCoverageItem = (
  coverageItem: CoverageItem,
  techniques: ('EP' | 'BVA' | 'DT')[]
): Promise<{ data: CoverageItem }> => {
  return apiClient.post('/blackbox/coverage/select-techniques', {
    coverage_item: coverageItem,
    techniques,
  });
};

/**
 * Get coverage report template structure
 */
export const getCoverageReportTemplate = (): Promise<{
  data: {
    total_coverage_items: number;
    covered_items: number;
    uncovered_items: number;
    coverage_percentage: number;
    type_distribution: Record<string, { total: number; covered: number }>;
    technique_usage: Record<string, number>;
    uncovered_item_details: Array<{ id: string; description: string; type: string }>;
  };
}> => {
  return apiClient.get('/blackbox/coverage/report-template');
};

export { apiClient };
