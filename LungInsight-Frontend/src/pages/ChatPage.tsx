import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import clsx from 'clsx';
import { MessageSquarePlus, MessageCircle, Trash2, Check, X, ImageOff } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { ListSkeleton } from '@/components/ui/Skeleton';
import {
  useChatSessions,
  useChatMessages,
  useSendChatMessage,
  useStartChatSession,
  useDeleteChatSession,
} from '@/hooks/useResources';
import { usePredictionImageUrl } from '@/hooks/usePredictions';
import { resolveImageUrl } from '@/lib/urls';
import { groupSessionsByDate } from '@/lib/chatGrouping';
import type { ChatSession } from '@/types';

interface ChatNavState {
  sessionId?: string;
  predictionId?: string;
}

interface SessionListItemProps {
  session: ChatSession;
  isActive: boolean;
  isConfirming: boolean;
  isDeleting: boolean;
  onSelect: () => void;
  onRequestDelete: () => void;
  onConfirmDelete: () => void;
  onCancelDelete: () => void;
}

function SessionListItem({
  session,
  isActive,
  isConfirming,
  isDeleting,
  onSelect,
  onRequestDelete,
  onConfirmDelete,
  onCancelDelete,
}: SessionListItemProps) {
  return (
    <li className="group relative">
      <button
        onClick={() => {
          if (isConfirming) return;
          onSelect();
        }}
        className={clsx(
          'flex w-full items-center gap-2.5 rounded-md px-3 py-2.5 pr-9 text-left text-sm transition-colors',
          isActive ? 'bg-cyan-50 text-cyan-700' : 'text-steel hover:bg-lightbox-dim'
        )}
      >
        <MessageCircle className={clsx('h-4 w-4 shrink-0', isActive ? 'text-cyan-600' : 'text-steel-light')} />
        <span className="truncate">{session.title}</span>
      </button>

      {isConfirming ? (
        <div className="absolute right-1.5 top-1/2 flex -translate-y-1/2 items-center gap-1">
          <button
            onClick={onConfirmDelete}
            disabled={isDeleting}
            title="Confirm delete"
            className="rounded p-1 text-red-600 hover:bg-red-50 disabled:opacity-50"
          >
            <Check className="h-3.5 w-3.5" />
          </button>
          <button onClick={onCancelDelete} title="Cancel" className="rounded p-1 text-steel hover:bg-lightbox-dim">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : (
        <button
          onClick={onRequestDelete}
          title="Delete conversation"
          className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded p-1 text-steel-light opacity-0 transition-opacity hover:bg-lightbox-dim hover:text-red-600 group-hover:opacity-100"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      )}
    </li>
  );
}

export function ChatPage() {
  const location = useLocation();
  const navState = (location.state as ChatNavState | null) ?? null;

  const { data: sessions, isLoading: sessionsLoading } = useChatSessions();
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>(navState?.sessionId);
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null);
  const { mutate: startSession, isPending: isStartingSession } = useStartChatSession();
  const { mutate: deleteSession, isPending: isDeleting } = useDeleteChatSession();

  useEffect(() => {
    if (activeSessionId || sessionsLoading) return;
    if (sessions && sessions.length > 0) {
      setActiveSessionId(sessions[0].id);
    } else if (sessions && sessions.length === 0 && !isStartingSession) {
      // No sessions yet (fresh real-backend user) — start one automatically
      // so the chat window is immediately usable instead of showing a dead end.
      startSession(undefined, { onSuccess: (session) => setActiveSessionId(session.id) });
    }
  }, [sessions, sessionsLoading, activeSessionId, isStartingSession, startSession]);

  // Derived, not separately tracked in state: prediction_id now persists on
  // the session itself (see chat_service.py), so the active session's own
  // data is the source of truth once it's loaded. Falls back to the
  // just-navigated-here value only for the brief window before the
  // freshly-created session appears in the sessions list.
  const activeSession = sessions?.find((s) => s.id === activeSessionId);
  const activePredictionId =
    activeSession?.predictionId ??
    (activeSessionId === navState?.sessionId ? navState?.predictionId : undefined) ??
    undefined;

  const { data: messages } = useChatMessages(activeSessionId);
  const { mutate: sendMessage, isPending } = useSendChatMessage(activeSessionId, activePredictionId);
  const { data: linkedImageUrl, isLoading: imageLoading } = usePredictionImageUrl(activePredictionId);

  const sessionGroups = groupSessionsByDate(sessions ?? []);

  function handleNewConversation() {
    startSession(undefined, { onSuccess: (session) => setActiveSessionId(session.id) });
  }

  function handleConfirmDelete(sessionId: string) {
    deleteSession(sessionId, {
      onSuccess: () => {
        setConfirmingDeleteId(null);
        if (activeSessionId === sessionId) setActiveSessionId(undefined);
      },
    });
  }

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">Chat</h1>
        <p className="text-sm text-steel">Ask about a prediction or clinical finding.</p>
      </div>

      <div className="grid h-[calc(100vh-13rem)] gap-6 lg:grid-cols-[280px_1fr]">
        <div className="hidden flex-col overflow-hidden rounded-lg border border-line bg-panel lg:flex">
          <button
            onClick={handleNewConversation}
            disabled={isStartingSession}
            className="flex items-center gap-2 border-b border-line px-4 py-3 text-sm font-medium text-cyan-600 transition-colors hover:bg-lightbox-dim disabled:opacity-50"
          >
            <MessageSquarePlus className="h-4 w-4" />
            New conversation
          </button>

          {sessionsLoading ? (
            <div className="p-3">
              <ListSkeleton rows={3} />
            </div>
          ) : sessions && sessions.length === 0 ? (
            <p className="p-4 text-center text-xs text-steel-light">No conversations yet.</p>
          ) : (
            <div className="flex-1 space-y-4 overflow-y-auto p-2">
              {sessionGroups.map((group) => (
                <div key={group.label}>
                  <p className="px-3 pb-1 pt-2 font-mono text-[10px] uppercase tracking-wide text-steel-light">
                    {group.label}
                  </p>
                  <ul className="space-y-0.5">
                    {group.sessions.map((session) => (
                      <SessionListItem
                        key={session.id}
                        session={session}
                        isActive={activeSessionId === session.id}
                        isConfirming={confirmingDeleteId === session.id}
                        isDeleting={isDeleting}
                        onSelect={() => setActiveSessionId(session.id)}
                        onRequestDelete={() => setConfirmingDeleteId(session.id)}
                        onConfirmDelete={() => handleConfirmDelete(session.id)}
                        onCancelDelete={() => setConfirmingDeleteId(null)}
                      />
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex min-h-0 flex-col gap-3">
          {activePredictionId && (
            <div className="flex items-center gap-3 rounded-lg border border-line bg-panel px-4 py-2.5">
              <div className="h-12 w-12 shrink-0 overflow-hidden rounded-md border border-line bg-lightbox-dim">
                {imageLoading ? (
                  <div className="flex h-full w-full items-center justify-center">
                    <ImageOff className="h-4 w-4 text-steel-light" />
                  </div>
                ) : (
                  <img
                    src={resolveImageUrl(linkedImageUrl)}
                    alt="Linked X-ray"
                    className="h-full w-full object-cover"
                  />
                )}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase tracking-wide text-steel-light">Linked prediction</p>
                <p className="truncate text-sm text-ink">{activeSession?.title}</p>
              </div>
            </div>
          )}

          <ChatWindow
            messages={messages ?? []}
            onSend={(content) => sendMessage(content)}
            isSending={isPending}
          />
        </div>
      </div>
    </AppShell>
  );
}
