import type {
  User,
  Prediction,
  HistoryItem,
  ChatSession,
  ChatMessage,
  DashboardSummary,
  PredictionLabel,
} from '@/types';

let idCounter = 1000;
function nextId(prefix: string): string {
  idCounter += 1;
  return `${prefix}-${idCounter.toString(36)}`;
}

export const mockUser: User = {
  id: 'user-mock-001',
  email: 'demo@lunginsight.ai',
  full_name: 'Demo User',
  is_active: true,
  created_at: '2026-06-01T09:00:00Z',
};

function randomLabel(): PredictionLabel {
  return Math.random() > 0.55 ? 'Pneumonia' : 'Normal';
}

function randomConfidence(label: PredictionLabel): number {
  // Pneumonia calls skew a bit more confident in the mock data, mirroring
  // the real model's higher recall than precision (see Module 1 MODEL.md).
  const base = label === 'Pneumonia' ? 82 : 75;
  return Math.round((base + Math.random() * 16) * 10) / 10;
}

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

export function generateMockHistory(count = 24): HistoryItem[] {
  return Array.from({ length: count }, (_, i) => {
    const label = randomLabel();
    return {
      prediction_id: nextId('pred'),
      image_filename: `xray_${String(i + 1).padStart(3, '0')}.jpg`,
      label,
      confidence: randomConfidence(label),
      heatmap_path: null,
      created_at: daysAgo(count - i),
    };
  }).reverse();
}

export function generateMockPredictions(count = 24): Prediction[] {
  return generateMockHistory(count).map((h) => ({
    id: h.prediction_id,
    image_id: nextId('img'),
    label: h.label,
    confidence: h.confidence,
    heatmap_path: h.heatmap_path,
    created_at: h.created_at,
  }));
}

export function mockPredictionResult(): Prediction {
  const label = randomLabel();
  return {
    id: nextId('pred'),
    image_id: nextId('img'),
    label,
    confidence: randomConfidence(label),
    heatmap_path: null,
    created_at: new Date().toISOString(),
  };
}

export const mockChatSessions: ChatSession[] = [
  {
    id: nextId('session'),
    title: 'Interpreting bilateral opacity',
    predictionId: null,
    created_at: daysAgo(5),
    updated_at: daysAgo(1),
  },
  {
    id: nextId('session'),
    title: 'Follow-up on case #0091',
    predictionId: null,
    created_at: daysAgo(10),
    updated_at: daysAgo(9),
  },
];

export const mockChatMessages: Record<string, ChatMessage[]> = {
  [mockChatSessions[0].id]: [
    {
      id: nextId('msg'),
      role: 'user',
      content: 'What does bilateral lower-lobe opacity usually indicate?',
      created_at: daysAgo(5),
    },
    {
      id: nextId('msg'),
      role: 'assistant',
      content:
        'Bilateral lower-lobe opacities are commonly associated with pneumonia, pulmonary edema, or aspiration. In the context of a positive pneumonia classification, this pattern is consistent with bronchopneumonia. Correlation with clinical symptoms and labs is recommended before treatment decisions.',
      created_at: daysAgo(5),
      citations: [
        {
          id: 'src-1',
          title: 'Radiographic Patterns in Community-Acquired Pneumonia',
          snippet: 'Bilateral lower-lobe involvement is observed in approximately 30% of bacterial pneumonia cases...',
        },
      ],
    },
  ],
};

export function buildDashboardSummary(history: HistoryItem[]): DashboardSummary {
  const totalPredictions = history.length;
  const averageConfidence =
    totalPredictions === 0
      ? 0
      : Math.round((history.reduce((sum, h) => sum + h.confidence, 0) / totalPredictions) * 10) / 10;

  const byDate = new Map<string, { sum: number; count: number }>();
  for (const item of history) {
    const day = item.created_at.slice(0, 10);
    const entry = byDate.get(day) ?? { sum: 0, count: 0 };
    entry.sum += item.confidence;
    entry.count += 1;
    byDate.set(day, entry);
  }
  const confidenceTrend = Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { sum, count }]) => ({
      date,
      averageConfidence: Math.round((sum / count) * 10) / 10,
    }));

  const normalCount = history.filter((h) => h.label === 'Normal').length;
  const pneumoniaCount = history.filter((h) => h.label === 'Pneumonia').length;

  return {
    totalPredictions,
    averageConfidence,
    recentUploads: history.slice(-5).reverse(),
    recentChats: mockChatSessions,
    confidenceTrend,
    distribution: [
      { label: 'Normal', count: normalCount },
      { label: 'Pneumonia', count: pneumoniaCount },
    ],
  };
}
