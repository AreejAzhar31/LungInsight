import { apiClient } from '@/lib/axios';
import { MOCK_MODE, mockDelay } from '@/lib/mock';
import { generateMockHistory } from '@/mocks/data';
import type { HistoryResponse } from '@/types';

let mockHistoryStore: ReturnType<typeof generateMockHistory> | null = null;
function getMockHistory() {
  if (!mockHistoryStore) mockHistoryStore = generateMockHistory(24);
  return mockHistoryStore;
}

export async function getHistory(page = 1, pageSize = 20): Promise<HistoryResponse> {
  if (MOCK_MODE) {
    await mockDelay();
    const all = getMockHistory();
    const start = (page - 1) * pageSize;
    return {
      items: all.slice(start, start + pageSize),
      total: all.length,
      page,
      page_size: pageSize,
    };
  }
  const { data } = await apiClient.get<HistoryResponse>('/api/v1/history', {
    params: { page, page_size: pageSize },
  });
  return data;
}
