import { useState, useRef, useEffect, type FormEvent } from 'react';
import { Send, Bot, User } from 'lucide-react';
import clsx from 'clsx';
import { SourceCitationCard } from '@/components/chat/SourceCitationCard';
import { Button } from '@/components/ui/Button';
import type { ChatMessage } from '@/types';

interface ChatWindowProps {
  messages: ChatMessage[];
  onSend: (content: string) => void;
  isSending?: boolean;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  } catch {
    return '';
  }
}

export function ChatWindow({ messages, onSend, isSending }: ChatWindowProps) {
  const [draft, setDraft] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!draft.trim() || isSending) return;
    onSend(draft.trim());
    setDraft('');
  }

  return (
    <div className="flex h-full flex-col rounded-lg border border-line bg-panel">
      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-3 py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-cyan-50">
              <Bot className="h-6 w-6 text-cyan-600" />
            </div>
            <p className="max-w-xs text-sm text-steel">
              Ask a question about a prediction or clinical finding to get started.
            </p>
          </div>
        )}
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div key={msg.id} className={clsx('flex items-end gap-2.5', isUser ? 'flex-row-reverse' : 'flex-row')}>
              <div
                className={clsx(
                  'flex h-7 w-7 shrink-0 items-center justify-center rounded-full',
                  isUser ? 'bg-cyan-500' : 'bg-lightbox-dim'
                )}
              >
                {isUser ? <User className="h-3.5 w-3.5 text-white" /> : <Bot className="h-3.5 w-3.5 text-cyan-600" />}
              </div>

              <div className={clsx('flex max-w-[75%] flex-col gap-1', isUser ? 'items-end' : 'items-start')}>
                <div
                  className={clsx(
                    'rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm',
                    isUser
                      ? 'rounded-br-sm bg-cyan-500 text-white'
                      : 'rounded-bl-sm border border-line bg-white text-ink'
                  )}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                <span className="px-1 text-[11px] text-steel-light">{formatTime(msg.created_at)}</span>

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-1 w-full space-y-2">
                    {msg.citations.map((c) => (
                      <SourceCitationCard key={c.id} citation={c} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {isSending && (
          <div className="flex items-end gap-2.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-lightbox-dim">
              <Bot className="h-3.5 w-3.5 text-cyan-600" />
            </div>
            <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm border border-line bg-white px-4 py-3 text-sm text-steel shadow-sm">
              <span>Thinking</span>
              <span className="flex gap-0.5">
                <span className="h-1 w-1 animate-bounce rounded-full bg-steel-light [animation-delay:-0.2s]" />
                <span className="h-1 w-1 animate-bounce rounded-full bg-steel-light [animation-delay:-0.1s]" />
                <span className="h-1 w-1 animate-bounce rounded-full bg-steel-light" />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-line p-3">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about a finding or prediction&hellip;"
          className="flex-1 rounded-md border border-line px-3.5 py-2.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          disabled={isSending}
        />
        <Button type="submit" disabled={!draft.trim() || isSending} aria-label="Send message">
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
