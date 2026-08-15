// No admin backend endpoints exist yet. Mocked here, shaped for an easy
// swap once user-management/moderation endpoints are added to the backend.

import { mockDelay } from '@/lib/mock';
import type { User } from '@/types';

export interface AdminUserRow extends User {
  predictionCount: number;
}

export async function listUsers(): Promise<AdminUserRow[]> {
  await mockDelay();
  return Array.from({ length: 12 }, (_, i) => ({
    id: `user-${i}`,
    email: `clinician${i + 1}@hospital.org`,
    full_name: `Clinician ${i + 1}`,
    is_active: i !== 4,
    created_at: new Date(Date.now() - i * 86400000 * 7).toISOString(),
    predictionCount: Math.floor(Math.random() * 60),
  }));
}
