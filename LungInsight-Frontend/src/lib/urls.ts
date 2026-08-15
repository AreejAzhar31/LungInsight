import { API_BASE_URL } from '@/lib/axios';
import { MOCK_MODE } from '@/lib/mock';
import { PLACEHOLDER_IMAGE } from '@/lib/placeholder';

/** The backend returns some paths relative to itself (e.g. local storage
 * mode's "/static/heatmaps/xyz.png" or "/uploads/xyz.jpg"), not full URLs —
 * the browser must resolve those against the backend's own origin, not the
 * frontend's. Supabase-mode signed URLs (and mock-mode URLs) are already
 * absolute and pass through unchanged. */
export function resolveBackendUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (MOCK_MODE || /^https?:\/\//.test(path)) return path;
  return `${API_BASE_URL}${path}`;
}

export function resolveImageUrl(url: string | null | undefined): string {
  return resolveBackendUrl(url) ?? PLACEHOLDER_IMAGE;
}
