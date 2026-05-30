import type { RequirementResponse, StructuredRequirement } from '../types/models';

type RequirementIdentity = {
  id: string;
  external_id?: string | null;
  title?: string | null;
};

/** Stable business id from import (e.g. LR-001), falling back to internal id. */
export function getRequirementRefId(requirement: RequirementIdentity): string {
  return requirement.external_id?.trim() || requirement.id;
}

/** Human-readable label for tables and queues. */
export function getRequirementDisplayName(requirement: RequirementIdentity): string {
  const ref = getRequirementRefId(requirement);
  const title = requirement.title?.trim();
  if (title) return `${ref} · ${title}`;
  return ref;
}

/** Map persisted requirement to FR 4.0/5.0 StructuredRequirement. */
export function toStructuredRequirement(row: RequirementResponse): StructuredRequirement {
  return {
    id: getRequirementRefId(row),
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
