import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getHistory } from '@/api/history';
import { getDashboardSummary } from '@/api/dashboard';
import { submitFeedback, type FeedbackPayload } from '@/api/feedback';
import { listChatSessions, getChatMessages, sendChatMessage, startChatSession, deleteChatSession } from '@/api/chat';
import { getHealth } from '@/api/health';
import { listUsers } from '@/api/admin';
import type { ChatMessage } from '@/types';

export function useHistory(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['history', page, pageSize],
    queryFn: () => getHistory(page, pageSize),
  });
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardSummary,
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: FeedbackPayload) => submitFeedback(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['predictions'] });
    },
  });
}

export function useChatSessions() {
  return useQuery({ queryKey: ['chat-sessions'], queryFn: listChatSessions });
}

export function useStartChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (predictionId?: string) => startChatSession(predictionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
    },
  });
}

export function useDeleteChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => deleteChatSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
    },
  });
}

export function useChatMessages(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['chat-messages', sessionId],
    queryFn: () => getChatMessages(sessionId as string),
    enabled: Boolean(sessionId),
  });
}

export function useSendChatMessage(sessionId: string | undefined, predictionId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => sendChatMessage(sessionId as string, content, predictionId),

    // Optimistic update: show the user's message immediately, don't wait
    // for the full round trip (RAG calls can take several seconds). Also
    // guarantees the message never silently vanishes if the request fails --
    // previously there was no onMutate/onError at all, so a failed request
    // just disappeared with no feedback.
    onMutate: async (content: string) => {
      if (!sessionId) return;
      const queryKey = ['chat-messages', sessionId];
      await queryClient.cancelQueries({ queryKey });
      const previousMessages = queryClient.getQueryData<ChatMessage[]>(queryKey) ?? [];

      const optimisticMessage: ChatMessage = {
        id: `optimistic-${Date.now()}`,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      };
      queryClient.setQueryData(queryKey, [...previousMessages, optimisticMessage]);

      return { previousMessages, queryKey };
    },

    onError: (_err, _content, context) => {
      // Roll back to the pre-send state and surface a real error message
      // in the conversation, instead of the message just disappearing.
      if (!context) return;
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "Sorry, that message couldn't be sent. Please check your connection and try again.",
        created_at: new Date().toISOString(),
      };
      queryClient.setQueryData(context.queryKey, [...context.previousMessages, errorMessage]);
    },

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', sessionId] });
      // The backend may have just auto-titled this session from the first
      // message (see chat_service.py's _generate_title) -- refresh the
      // sidebar list so the new title actually shows up there.
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
    },
  });
}

export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: getHealth, refetchInterval: 30_000 });
}

export function useAdminUsers() {
  return useQuery({ queryKey: ['admin-users'], queryFn: listUsers });
}
