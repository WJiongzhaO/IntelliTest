import apiClient from './client';
import type { RiskDashboardSummary } from '../types/models';

export async function getRiskDashboard(topN = 5): Promise<RiskDashboardSummary> {
  const { data } = await apiClient.get<RiskDashboardSummary>('/risk/dashboard', {
    params: { top_n: topN },
  });
  return data;
}
