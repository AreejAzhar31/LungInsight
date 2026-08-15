import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatWindow } from '@/components/chat/ChatWindow';
import type { ChatMessage } from '@/types';

const sampleMessages: ChatMessage[] = [
  { id: '1', role: 'user', content: 'What does this finding mean?', created_at: '2026-08-01T00:00:00Z' },
  {
    id: '2',
    role: 'assistant',
    content: 'This suggests bilateral opacity.',
    created_at: '2026-08-01T00:01:00Z',
    citations: [{ id: 'c1', title: 'Clinical Reference', snippet: 'Relevant snippet text.' }],
  },
];

describe('ChatWindow', () => {
  it('shows an empty-state prompt with no messages', () => {
    render(<ChatWindow messages={[]} onSend={vi.fn()} />);
    expect(screen.getByText(/ask a question about a prediction/i)).toBeInTheDocument();
  });

  it('renders all messages and citations', () => {
    render(<ChatWindow messages={sampleMessages} onSend={vi.fn()} />);
    expect(screen.getByText('What does this finding mean?')).toBeInTheDocument();
    expect(screen.getByText('This suggests bilateral opacity.')).toBeInTheDocument();
    expect(screen.getByText('Clinical Reference')).toBeInTheDocument();
  });

  it('calls onSend with the typed message and clears the input', async () => {
    const onSend = vi.fn();
    render(<ChatWindow messages={[]} onSend={onSend} />);
    const input = screen.getByPlaceholderText(/ask about a finding/i);
    await userEvent.type(input, 'Is this urgent?');
    await userEvent.click(screen.getByRole('button', { name: /send message/i }));
    expect(onSend).toHaveBeenCalledWith('Is this urgent?');
    expect(input).toHaveValue('');
  });

  it('does not call onSend for an empty message', async () => {
    const onSend = vi.fn();
    render(<ChatWindow messages={[]} onSend={onSend} />);
    expect(screen.getByRole('button', { name: /send message/i })).toBeDisabled();
  });

  it('disables the input while sending', () => {
    render(<ChatWindow messages={[]} onSend={vi.fn()} isSending />);
    expect(screen.getByPlaceholderText(/ask about a finding/i)).toBeDisabled();
    expect(screen.getByText(/thinking/i)).toBeInTheDocument();
  });
});
