import { describe, it, expect } from 'vitest';
import { createPrediction, getPrediction, listPredictions } from '@/api/predictions';

describe('predictions API (mock mode)', () => {
  it('createPrediction returns a prediction with a valid label and confidence range', async () => {
    const file = new File(['data'], 'xray.jpg', { type: 'image/jpeg' });
    const result = await createPrediction(file);

    expect(['Normal', 'Pneumonia']).toContain(result.label);
    expect(result.confidence).toBeGreaterThanOrEqual(0);
    expect(result.confidence).toBeLessThanOrEqual(100);
    expect(result.id).toBeTruthy();
  });

  it('getPrediction retrieves a previously created prediction by id', async () => {
    const file = new File(['data'], 'xray.jpg', { type: 'image/jpeg' });
    const created = await createPrediction(file);
    const fetched = await getPrediction(created.id);
    expect(fetched.id).toBe(created.id);
  });

  it('getPrediction throws for an unknown id', async () => {
    await expect(getPrediction('does-not-exist')).rejects.toThrow('Prediction not found.');
  });

  it('listPredictions respects page and page_size', async () => {
    const result = await listPredictions(1, 5);
    expect(result.items.length).toBeLessThanOrEqual(5);
    expect(result.page).toBe(1);
    expect(result.page_size).toBe(5);
    expect(result.total).toBeGreaterThan(0);
  });
});
