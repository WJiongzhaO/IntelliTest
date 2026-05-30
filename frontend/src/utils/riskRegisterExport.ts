import type { RequirementResponse } from '../types/models';
import { getRequirementRefId } from './requirementMapper';

/**
 * Columns aligned with FR 2.0 persisted risk fields on RequirementResponse
 * (same shape as fixtures/juice-shop/risk_register.csv).
 */
export const RISK_REGISTER_HEADERS = [
  'ID',
  'title',
  'impact',
  'likelihood',
  'risk_score',
  'priority',
  'impact_rationale',
  'likelihood_rationale',
] as const;

export type RiskRegisterRow = Record<(typeof RISK_REGISTER_HEADERS)[number], string>;

export function requirementToRiskRegisterRow(req: RequirementResponse): RiskRegisterRow | null {
  if (
    req.risk_impact == null ||
    req.risk_likelihood == null ||
    req.risk_score == null ||
    !req.priority
  ) {
    return null;
  }

  const id = getRequirementRefId(req);
  const title = req.title?.trim() || req.raw_text.slice(0, 120);

  return {
    ID: id,
    title,
    impact: String(req.risk_impact),
    likelihood: String(req.risk_likelihood),
    risk_score: String(req.risk_score),
    priority: req.priority,
    impact_rationale: req.risk_impact_rationale?.trim() || '',
    likelihood_rationale: req.risk_likelihood_rationale?.trim() || '',
  };
}

function escapeCsvCell(value: string): string {
  if (/[",\r\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function buildRiskRegisterCsv(rows: RiskRegisterRow[]): string {
  const lines = [RISK_REGISTER_HEADERS.join(',')];
  for (const row of rows) {
    lines.push(
      RISK_REGISTER_HEADERS.map((key) => escapeCsvCell(row[key] ?? '')).join(','),
    );
  }
  return lines.join('\r\n');
}

export function downloadRiskRegisterCsv(rows: RiskRegisterRow[], filename = 'risk_register.csv') {
  const csv = buildRiskRegisterCsv(rows);
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
