// Shared types. Field names/shapes deliberately mirror the backend's
// Pydantic schemas 1:1 (see LungInsight-Backend/docs/API.md) so swapping
// mock data for real API responses requires no type changes.

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterResponse {
  user: User;
  tokens: TokenResponse;
}

export type PredictionLabel = 'Normal' | 'Pneumonia';

export interface Prediction {
  id: string;
  image_id: string;
  label: PredictionLabel;
  confidence: number; // 0-100
  heatmap_path: string | null;
  created_at: string;
}

export interface PredictionListResponse {
  items: Prediction[];
  total: number;
  page: number;
  page_size: number;
}

export interface HistoryItem {
  prediction_id: string;
  image_filename: string;
  label: PredictionLabel;
  confidence: number;
  heatmap_path: string | null;
  created_at: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface Feedback {
  id: string;
  prediction_id: string;
  rating: number; // 1-5
  comment: string | null;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  database: string;
}

// ---- Frontend-only types (chat + RAG citations, not yet backed by an API module) ----

export interface SourceCitation {
  id: string;
  title: string;
  snippet: string;
  url?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  citations?: SourceCitation[];
}

export interface ChatSession {
  id: string;
  title: string;
  predictionId: string | null;
  created_at: string;
  updated_at: string;
}

// ---- Dashboard aggregate types ----

export interface ConfidenceTrendPoint {
  date: string;
  averageConfidence: number;
}

export interface DistributionSlice {
  label: PredictionLabel;
  count: number;
}

export interface DashboardSummary {
  totalPredictions: number;
  averageConfidence: number;
  recentUploads: HistoryItem[];
  recentChats: ChatSession[];
  confidenceTrend: ConfidenceTrendPoint[];
  distribution: DistributionSlice[];
}
