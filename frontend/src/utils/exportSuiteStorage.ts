import type { TestSuite } from '../types/models';

export const EXPORT_SUITE_STORAGE_KEY = 'intellitest_last_suite';
export const REVIEW_SUITE_STORAGE_KEY = 'intellitest_review_suite';
export const REVIEW_HISTORY_STORAGE_KEY = 'intellitest_review_history';

export function saveSuiteForReviewExport(suite: TestSuite) {
  sessionStorage.setItem(EXPORT_SUITE_STORAGE_KEY, JSON.stringify(suite));
  sessionStorage.removeItem(REVIEW_SUITE_STORAGE_KEY);
  sessionStorage.removeItem(REVIEW_HISTORY_STORAGE_KEY);
}
