import { describe, it, expect } from 'vitest';
import {
  listChatSessions,
  startChatSession,
  getChatMessages,
  sendChatMessage,
  resetChatSession,
} from '@/api/chat';

describe('chat API (mock mode)', () => {
  it('startChatSession creates a session that appears at the front of the list', async () => {
    const session = await startChatSession();
    const after = await listChatSessions();

    expect(session.id).toBeTruthy();
    expect(after[0].id).toBe(session.id);
  });

  it('sendChatMessage appends a user message and an assistant reply with citations', async () => {
    const session = await startChatSession();
    const reply = await sendChatMessage(session.id, 'What does this mean?');

    expect(reply.role).toBe('assistant');
    expect(reply.content.length).toBeGreaterThan(0);
    expect(reply.citations?.length ?? 0).toBeGreaterThan(0);

    const messages = await getChatMessages(session.id);
    expect(messages.length).toBe(2);
    expect(messages[0].role).toBe('user');
    expect(messages[1].role).toBe('assistant');
  });

  it('resetChatSession clears message history for that session', async () => {
    const session = await startChatSession();
    await sendChatMessage(session.id, 'hello');
    expect((await getChatMessages(session.id)).length).toBe(2);

    await resetChatSession(session.id);
    expect((await getChatMessages(session.id)).length).toBe(0);
  });
});
