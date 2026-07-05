"use client";

import { useCallback, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendReportChatMessage } from "@/lib/api";
import type { ChatTurn } from "@/types/api";

interface SendVariables {
  message: string;
  conversation: ChatTurn[];
}

/**
 * Drives one report's AI Copilot conversation. Entirely client-side state
 * -- nothing is persisted (Phase 8 scope: "No conversation persistence,
 * No memory"), so refreshing the page starts a fresh conversation. Each
 * request resends the full transcript so far, since the backend itself
 * holds no state between calls.
 */
export function useReportChat(reportId: string) {
  const [conversation, setConversation] = useState<ChatTurn[]>([]);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: ({ message, conversation: priorConversation }: SendVariables) =>
      sendReportChatMessage(reportId, message, priorConversation),
  });

  const sendMessage = useCallback(
    (message: string) => {
      const trimmed = message.trim();
      if (!trimmed || mutation.isPending) return;

      const priorConversation = conversation;
      setLastFailedMessage(null);
      setConversation((prev) => [...prev, { role: "user", content: trimmed }]);

      mutation.mutate(
        { message: trimmed, conversation: priorConversation },
        {
          onSuccess: (data) => {
            setConversation((prev) => [...prev, { role: "assistant", content: data.reply }]);
          },
          onError: () => {
            setLastFailedMessage(trimmed);
          },
        },
      );
    },
    [conversation, mutation],
  );

  const retry = useCallback(() => {
    if (!lastFailedMessage) return;
    const messageToRetry = lastFailedMessage;
    // The failed user turn is already in `conversation` (appended optimistically
    // in sendMessage) -- drop it here so it isn't duplicated in the transcript.
    const priorConversation = conversation.slice(0, -1);
    setLastFailedMessage(null);

    mutation.mutate(
      { message: messageToRetry, conversation: priorConversation },
      {
        onSuccess: (data) => {
          setConversation((prev) => [...prev, { role: "assistant", content: data.reply }]);
        },
        onError: () => {
          setLastFailedMessage(messageToRetry);
        },
      },
    );
  }, [conversation, lastFailedMessage, mutation]);

  const clear = useCallback(() => {
    setConversation([]);
    setLastFailedMessage(null);
    mutation.reset();
  }, [mutation]);

  return {
    conversation,
    sendMessage,
    retry,
    clear,
    isSending: mutation.isPending,
    canRetry: lastFailedMessage != null,
    error: mutation.isError ? mutation.error : null,
  };
}
