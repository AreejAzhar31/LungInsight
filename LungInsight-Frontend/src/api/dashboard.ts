import { MOCK_MODE, mockDelay } from '@/lib/mock';
import { generateMockHistory, buildDashboardSummary } from '@/mocks/data';
import { getHistory } from '@/api/history';
import type { DashboardSummary } from '@/types';

export async function getDashboardSummary(): Promise<DashboardSummary> {
  if (MOCK_MODE) {
    await mockDelay();
    return buildDashboardSummary(generateMockHistory(30));
  }
  // No dedicated dashboard-aggregate endpoint exists on the backend yet;
  // derive the summary client-side from /api/v1/history in the meantime.
  const history = await getHistory(1, 100);
  return buildDashboardSummary(history.items);
}
