import { describe, it, expect } from 'vitest';
import { groupSessionsByDate } from '@/lib/chatGrouping';
import type { ChatSession } from '@/types';

function makeSession(id: string, hoursAgo: number): ChatSession {
  const date = new Date();
  date.setHours(date.getHours() - hoursAgo);
  return {
    id,
    title: `Session ${id}`,
    predictionId: null,
    created_at: date.toISOString(),
    updated_at: date.toISOString(),
  };
}

describe('groupSessionsByDate', () => {
  it('groups a session from a few minutes ago under Today', () => {
    const groups = groupSessionsByDate([makeSession('a', 0.1)]);
    expect(groups).toHaveLength(1);
    expect(groups[0].label).toBe('Today');
  });

  it('groups a session from ~30 hours ago under Yesterday', () => {
    const groups = groupSessionsByDate([makeSession('a', 30)]);
    expect(groups[0].label).toBe('Yesterday');
  });

  it('groups a session from 10 days ago under Previous 30 Days', () => {
    const groups = groupSessionsByDate([makeSession('a', 24 * 10)]);
    expect(groups[0].label).toBe('Previous 30 Days');
  });

  it('groups a session from 60 days ago under Older', () => {
    const groups = groupSessionsByDate([makeSession('a', 24 * 60)]);
    expect(groups[0].label).toBe('Older');
  });

  it('sorts sessions within each group by most recently updated first', () => {
    const older = makeSession('older', 5);
    const newer = makeSession('newer', 1);
    const groups = groupSessionsByDate([older, newer]);
    expect(groups[0].sessions.map((s) => s.id)).toEqual(['newer', 'older']);
  });

  it('omits empty groups entirely', () => {
    const groups = groupSessionsByDate([makeSession('a', 0.1)]);
    expect(groups.map((g) => g.label)).toEqual(['Today']);
  });

  it('returns an empty array for no sessions', () => {
    expect(groupSessionsByDate([])).toEqual([]);
  });
});
