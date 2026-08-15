// Wired to the real backend /api/v1/chat/* endpoints (see PredictionService's
// counterpart chat_service.py). Falls back to mock data when MOCK_MODE is on,
// same pattern as predictions.ts / auth.ts.

import { apiClient } from '@/lib/axios';
import { MOCK_MODE, mockDelay } from '@/lib/mock';
import { mockChatSessions, mockChatMessages } from '@/mocks/data';
import type { ChatSession, ChatMessage, SourceCitation } from '@/types';

// ---- backend response shapes (snake_case, differ slightly from frontend types) ----

interface BackendChatSession {
  id: string;
  prediction_id: string | null;
  title: string | null;
  created_at: string;
  updated_at: string;
}

interface BackendChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

interface BackendRetrievedChunk {
  source?: string;
  text?: string;
  score?: number;
}

interface BackendChatTurnResponse {
  session_id: string;
  answer: string;
  citations: BackendRetrievedChunk[];
  is_safe: boolean;
  safety_reason?: string | null;
  verification_passed?: boolean | null;
}

function toSession(s: BackendChatSession): ChatSession {
  return {
    id: s.id,
    title: s.title ?? 'New conversation',
    predictionId: s.prediction_id,
    created_at: s.created_at,
    updated_at: s.updated_at,
  };
}

function toCitations(chunks: BackendRetrievedChunk[]): SourceCitation[] {
  return chunks.map((c, i) => ({
    id: `${i}-${c.source ?? 'source'}`,
    title: c.source ?? 'Clinical knowledge base',
    snippet: c.text ?? '',
  }));
}

// The RAG service embeds [cite:chunk_id] markers inline in its answer text
// so its own safety-verification step can check every claim is sourced
// (see rag/agent/safety.py) — that's deliberate and shouldn't be removed
// server-side. But those raw tags are meant for machine verification, not
// for display: strip them here and show the same sources as clean cards
// underneath instead (citations array, already returned separately).
function stripInlineCitationTags(text: string): string {
  return text
    .replace(/\s*\[cite:[^\]]+\]/g, '')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
}

// ---- public API ----

export async function listChatSessions(): Promise<ChatSession[]> {
  if (MOCK_MODE) {
    await mockDelay();
    return mockChatSessions;
  }
  const { data } = await apiClient.get<BackendChatSession[]>('/api/v1/chat/sessions');
  return data.map(toSession);
}

/** Starts a new chat session. Pass predictionId to ground the assistant's
 * answers in that prediction's result (recommended right after a user views
 * a prediction and opens chat from there). */
export async function startChatSession(predictionId?: string): Promise<ChatSession> {
  if (MOCK_MODE) {
    await mockDelay();
    const session: ChatSession = {
      id: `session-${Date.now()}`,
      title: predictionId ? 'Prediction follow-up' : 'New conversation',
      predictionId: predictionId ?? null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mockChatSessions.unshift(session);
    return session;
  }
  const { data } = await apiClient.post<BackendChatSession>('/api/v1/chat/sessions', {
    prediction_id: predictionId ?? null,
  });
  return toSession(data);
}

export async function getChatMessages(sessionId: string): Promise<ChatMessage[]> {
  if (MOCK_MODE) {
    await mockDelay();
    return mockChatMessages[sessionId] ?? [];
  }
  const { data } = await apiClient.get<BackendChatMessage[]>(
    `/api/v1/chat/sessions/${sessionId}/messages`
  );
  return data.map((m) => ({
    id: m.id,
    role: m.role === 'system' ? 'assistant' : m.role,
    content: m.role === 'assistant' ? stripInlineCitationTags(m.content) : m.content,
    created_at: m.created_at,
  }));
}

/** Send a message in an existing session. Pass predictionId on the first
 * turn only — the backend/RAG service remembers it for later turns. */
export async function sendChatMessage(
  sessionId: string,
  content: string,
  predictionId?: string
): Promise<ChatMessage> {
  if (MOCK_MODE) {
    await mockDelay(900);
    const reply: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content:
        "This is a placeholder response. Once the chat/RAG module is connected, this will be a real answer grounded in the patient's prediction history and cited clinical sources.",
      created_at: new Date().toISOString(),
      citations: [
        {
          id: 'src-placeholder',
          title: 'Placeholder source',
          snippet: 'Real citations will appear here once the RAG module is wired in.',
        },
      ],
    };
    if (!mockChatMessages[sessionId]) mockChatMessages[sessionId] = [];
    mockChatMessages[sessionId].push(
      { id: `msg-${Date.now()}-u`, role: 'user', content, created_at: new Date().toISOString() },
      reply
    );
    return reply;
  }

  const { data } = await apiClient.post<BackendChatTurnResponse>(
    `/api/v1/chat/sessions/${sessionId}/messages`,
    { message: content, prediction_id: predictionId ?? null }
  );

  return {
    id: `msg-${data.session_id}-${Date.now()}`, // backend doesn't return a message id, only session_id
    role: 'assistant',
    content: data.is_safe
      ? stripInlineCitationTags(data.answer)
      : stripInlineCitationTags(data.answer) || "I can't answer that safely — " + (data.safety_reason ?? 'please rephrase.'),
    created_at: new Date().toISOString(),
    citations: toCitations(data.citations),
  };
}

export async function resetChatSession(sessionId: string): Promise<void> {
  if (MOCK_MODE) {
    await mockDelay();
    delete mockChatMessages[sessionId];
    return;
  }
  await apiClient.post(`/api/v1/chat/sessions/${sessionId}/reset`);
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  if (MOCK_MODE) {
    await mockDelay();
    const idx = mockChatSessions.findIndex((s) => s.id === sessionId);
    if (idx !== -1) mockChatSessions.splice(idx, 1);
    delete mockChatMessages[sessionId];
    return;
  }
  await apiClient.delete(`/api/v1/chat/sessions/${sessionId}`);
}
