import type { BlackBoxGenerationResult } from '../types/models';

export function mergeBlackboxResults(results: BlackBoxGenerationResult[]): BlackBoxGenerationResult | null {
  if (results.length === 0) return null;

  const test_cases = results.flatMap((r) => r.test_cases);
  const coverage_items = results.flatMap((r) => r.coverage_items);

  const total = coverage_items.length;
  const coveredIds = new Set<string>();
  for (const result of results) {
    for (const item of result.coverage_items) {
      if (item.covered_by_test_cases.length > 0) coveredIds.add(item.id);
    }
  }
  const covered = coveredIds.size;

  const type_distribution: Record<string, { total: number; covered: number }> = {};
  const technique_usage: Record<string, number> = {};
  const uncovered_item_details: Array<{ id: string; description: string; type: string }> = [];

  for (const result of results) {
    for (const [type, stats] of Object.entries(result.coverage_report.type_distribution)) {
      const current = type_distribution[type] ?? { total: 0, covered: 0 };
      type_distribution[type] = {
        total: current.total + stats.total,
        covered: current.covered + stats.covered,
      };
    }
    for (const [technique, count] of Object.entries(result.coverage_report.technique_usage)) {
      technique_usage[technique] = (technique_usage[technique] ?? 0) + count;
    }
    uncovered_item_details.push(...result.coverage_report.uncovered_item_details);
  }

  return {
    test_cases,
    coverage_items,
    coverage_report: {
      total_coverage_items: total,
      covered_items: covered,
      uncovered_items: total - covered,
      coverage_percentage: total > 0 ? (covered / total) * 100 : 0,
      type_distribution,
      technique_usage,
      uncovered_item_details,
    },
  };
}
