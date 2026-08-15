import type { ChatSession } from '@/types';

export interface ChatSessionGroup {
  label: string;
  sessions: ChatSession[];
}

/** Groups sessions into "Today / Yesterday / Previous 7 Days / Previous 30
 * Days / Older" buckets by updated_at, most recent activity first within
 * each bucket. Same pattern as ChatGPT/Claude's own sidebar. */
export function groupSessionsByDate(sessions: ChatSession[]): ChatSessionGroup[] {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);
  const sevenDaysAgo = new Date(startOfToday);
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  const thirtyDaysAgo = new Date(startOfToday);
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const buckets: Record<string, ChatSession[]> = {
    Today: [],
    Yesterday: [],
    'Previous 7 Days': [],
    'Previous 30 Days': [],
    Older: [],
  };

  const sorted = [...sessions].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );

  for (const session of sorted) {
    const updated = new Date(session.updated_at);
    if (updated >= startOfToday) {
      buckets.Today.push(session);
    } else if (updated >= startOfYesterday) {
      buckets.Yesterday.push(session);
    } else if (updated >= sevenDaysAgo) {
      buckets['Previous 7 Days'].push(session);
    } else if (updated >= thirtyDaysAgo) {
      buckets['Previous 30 Days'].push(session);
    } else {
      buckets.Older.push(session);
    }
  }

  return Object.entries(buckets)
    .filter(([, group]) => group.length > 0)
    .map(([label, group]) => ({ label, sessions: group }));
}
