import type { RequirementResponse, StructuredRequirement } from '../types/models';

/** Map member A/B persisted requirement to FR 4.0/5.0 StructuredRequirement. */
export function toStructuredRequirement(row: RequirementResponse): StructuredRequirement {
  return {
    id: row.id,
    title: row.title ?? undefined,
    raw_text: row.raw_text,
    input_fields: row.input_fields ?? [],
    data_ranges: row.data_ranges ?? [],
    conditions: row.conditions ?? [],
    expected_actions: row.expected_actions ?? [],
    risk_score: row.risk_score ?? undefined,
    priority: row.priority ?? undefined,
  };
}

export function getRequirementDisplayName(
  requirement: { id: string; title?: string | null },
): string {
  return requirement.title?.trim() || requirement.id;
}
