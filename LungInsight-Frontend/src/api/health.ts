import { apiClient } from '@/lib/axios';
import { MOCK_MODE, mockDelay } from '@/lib/mock';
import type { HealthResponse } from '@/types';

export async function getHealth(): Promise<HealthResponse> {
  if (MOCK_MODE) {
    await mockDelay(150);
    return { status: 'ok', app_name: 'LungInsight AI Backend', database: 'connected' };
  }
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
}
