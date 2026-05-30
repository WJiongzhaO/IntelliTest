import type { CoverageItem, TestCase } from '../types/models';

/** Recompute covered_by_test_cases from remaining test cases. */
export function syncCoverageFromCases(
  coverageItems: CoverageItem[],
  testCases: TestCase[],
): CoverageItem[] {
  const caseIds = new Set(testCases.map((tc) => tc.id));
  const coverers = new Map<string, string[]>();

  for (const tc of testCases) {
    for (const covId of tc.coverage_items ?? []) {
      const list = coverers.get(covId) ?? [];
      list.push(tc.id);
      coverers.set(covId, list);
    }
  }

  return coverageItems.map((item) => ({
    ...item,
    covered_by_test_cases: (coverers.get(item.id) ?? []).filter((id) => caseIds.has(id)),
  }));
}

export function nextManualCaseId(requirementRef: string, existing: TestCase[]): string {
  const prefix = `${requirementRef}_MANUAL_`;
  const ids = new Set(existing.map((c) => c.id));
  for (let n = 1; n <= 999; n += 1) {
    const id = `${prefix}${String(n).padStart(3, '0')}`;
    if (!ids.has(id)) return id;
  }
  return `${prefix}${Date.now()}`;
}

export function createManualTestCase(requirementRef: string, existing: TestCase[]): TestCase {
  return {
    id: nextManualCaseId(requirementRef, existing),
    requirement_id: requirementRef,
    title: '新建测试用例',
    test_steps: [],
    priority: 'Medium',
    coverage_items: [],
    modified_by_user: true,
  };
}
