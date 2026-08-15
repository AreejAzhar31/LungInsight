import { describe, it, expect } from 'vitest';
import { generateMockHistory, buildDashboardSummary } from '@/mocks/data';

describe('generateMockHistory', () => {
  it('generates the requested number of items', () => {
    expect(generateMockHistory(10)).toHaveLength(10);
  });

  it('generates items with valid labels', () => {
    const history = generateMockHistory(20);
    for (const item of history) {
      expect(['Normal', 'Pneumonia']).toContain(item.label);
      expect(item.confidence).toBeGreaterThanOrEqual(0);
      expect(item.confidence).toBeLessThanOrEqual(100);
    }
  });

  it('generates unique prediction ids', () => {
    const history = generateMockHistory(15);
    const ids = new Set(history.map((h) => h.prediction_id));
    expect(ids.size).toBe(15);
  });
});

describe('buildDashboardSummary', () => {
  it('computes correct totals and averages', () => {
    const history = generateMockHistory(10);
    const summary = buildDashboardSummary(history);

    expect(summary.totalPredictions).toBe(10);
    expect(summary.averageConfidence).toBeGreaterThan(0);
    expect(summary.recentUploads.length).toBeLessThanOrEqual(5);
  });

  it('handles an empty history without dividing by zero', () => {
    const summary = buildDashboardSummary([]);
    expect(summary.totalPredictions).toBe(0);
    expect(summary.averageConfidence).toBe(0);
    expect(summary.recentUploads).toHaveLength(0);
  });

  it('splits distribution counts correctly between Normal and Pneumonia', () => {
    const history = generateMockHistory(30);
    const summary = buildDashboardSummary(history);
    const normal = summary.distribution.find((d) => d.label === 'Normal')?.count ?? 0;
    const pneumonia = summary.distribution.find((d) => d.label === 'Pneumonia')?.count ?? 0;
    expect(normal + pneumonia).toBe(30);
  });
});
