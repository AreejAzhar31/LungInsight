import { apiClient } from '@/lib/axios';
import { MOCK_MODE, mockDelay } from '@/lib/mock';
import { PLACEHOLDER_IMAGE } from '@/lib/placeholder';
import { generateMockPredictions, mockPredictionResult } from '@/mocks/data';
import type { Prediction, PredictionListResponse } from '@/types';

let mockStore: Prediction[] | null = null;
function getMockStore(): Prediction[] {
  if (!mockStore) mockStore = generateMockPredictions(24);
  return mockStore;
}

export async function createPrediction(file: File): Promise<Prediction> {
  if (MOCK_MODE) {
    await mockDelay(1200); // upload + inference both take real time; mimic that
    const result = mockPredictionResult();
    getMockStore().unshift(result);
    return result;
  }
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<Prediction>('/api/v1/prediction', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getPrediction(id: string): Promise<Prediction> {
  if (MOCK_MODE) {
    await mockDelay();
    const found = getMockStore().find((p) => p.id === id);
    if (!found) throw new Error('Prediction not found.');
    return found;
  }
  const { data } = await apiClient.get<Prediction>(`/api/v1/prediction/${id}`);
  return data;
}

/** Fetches a viewable URL for the original uploaded X-ray. In Supabase
 * storage mode this is a time-limited signed URL (the bucket is private),
 * so don't cache it long-term -- refetch if it might have expired. */
export async function getPredictionImageUrl(id: string): Promise<string> {
  if (MOCK_MODE) {
    await mockDelay(150);
    // No real uploaded file in mock mode -- same placeholder chest X-ray
    // silhouette used everywhere else in mock data.
    return PLACEHOLDER_IMAGE;
  }
  const { data } = await apiClient.get<{ url: string }>(`/api/v1/prediction/${id}/image-url`);
  return data.url;
}

export async function listPredictions(page = 1, pageSize = 20): Promise<PredictionListResponse> {
  if (MOCK_MODE) {
    await mockDelay();
    const all = getMockStore();
    const start = (page - 1) * pageSize;
    return {
      items: all.slice(start, start + pageSize),
      total: all.length,
      page,
      page_size: pageSize,
    };
  }
  const { data } = await apiClient.get<PredictionListResponse>('/api/v1/predictions', {
    params: { page, page_size: pageSize },
  });
  return data;
}
