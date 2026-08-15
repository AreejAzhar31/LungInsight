import { apiClient } from '@/lib/axios';
import { MOCK_MODE, mockDelay } from '@/lib/mock';
import type { Feedback } from '@/types';

export interface FeedbackPayload {
  prediction_id: string;
  rating: number;
  comment?: string;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<Feedback> {
  if (MOCK_MODE) {
    await mockDelay(400);
    return {
      id: `feedback-${Date.now()}`,
      prediction_id: payload.prediction_id,
      rating: payload.rating,
      comment: payload.comment ?? null,
      created_at: new Date().toISOString(),
    };
  }
  const { data } = await apiClient.post<Feedback>('/api/v1/feedback', payload);
  return data;
}
