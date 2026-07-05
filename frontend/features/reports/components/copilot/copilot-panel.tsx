"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRightCircle, Eraser, FileText, Lightbulb, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatInput } from "@/features/reports/components/copilot/chat-input";
import { ChatMessage } from "@/features/reports/components/copilot/chat-message";
import { SuggestedPrompt } from "@/features/reports/components/copilot/suggested-prompt";
import { TypingIndicator } from "@/features/reports/components/copilot/typing-indicator";
import { useReportChat } from "@/hooks/use-report-chat";
import { ApiError } from "@/lib/api";

const SUGGESTED_PROMPTS = [
  { icon: FileText, label: "Summarize report", message: "Summarize this report." },
  { icon: AlertTriangle, label: "Highest risk issues", message: "What are the critical violations?" },
  { icon: Lightbulb, label: "Explain recommendations", message: "What should I fix first?" },
  { icon: ArrowRightCircle, label: "Next steps", message: "What are my next steps to become compliant?" },
] as const;

interface CopilotPanelProps {
  reportId: string;
  onClose: () => void;
}

/**
 * The AI Copilot's chat surface -- shared by the desktop sidebar and the
 * mobile bottom sheet (see `copilot-launcher.tsx`), which just wrap this
 * in different positioning chrome.
 */
export function CopilotPanel({ reportId, onClose }: CopilotPanelProps) {
  const { conversation, sendMessage, retry, clear, isSending, canRetry, error } = useReportChat(reportId);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [conversation, isSending]);

  return (
    <div className="flex h-full flex-col bg-popover">
      <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="size-4 text-primary" aria-hidden="true" />
          </span>
          <span className="text-sm font-semibold tracking-tight text-foreground">AI Copilot</span>
        </div>
        <div className="flex items-center gap-1">
          {conversation.length > 0 && (
            <Button variant="ghost" size="icon-sm" aria-label="Clear conversation" onClick={clear}>
              <Eraser className="size-4" />
            </Button>
          )}
          <Button variant="ghost" size="icon-sm" aria-label="Close AI Copilot" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        {conversation.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="flex h-full flex-col justify-center gap-6"
          >
            <div className="flex flex-col items-center gap-3 text-center">
              <span className="flex size-12 items-center justify-center rounded-full bg-primary/10">
                <Sparkles className="size-5 text-primary" aria-hidden="true" />
              </span>
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Ask about this report</p>
                <p className="text-xs text-muted-foreground">
                  The Copilot answers using only this report&apos;s findings, summary, and sources -- nothing else.
                </p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Try asking</p>
              {SUGGESTED_PROMPTS.map((prompt) => (
                <SuggestedPrompt
                  key={prompt.label}
                  icon={prompt.icon}
                  label={prompt.label}
                  onSelect={() => sendMessage(prompt.message)}
                />
              ))}
            </div>
          </motion.div>
        ) : (
          <div className="space-y-4">
            {conversation.map((turn, index) => (
              <ChatMessage key={index} turn={turn} />
            ))}
            {isSending && (
              <div className="flex gap-2">
                <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                  <Sparkles className="size-3.5" aria-hidden="true" />
                </span>
                <TypingIndicator />
              </div>
            )}
            {error && !isSending && (
              <div className="flex flex-col gap-2 rounded-lg border border-critical/20 bg-critical/5 px-3 py-2.5 text-xs text-foreground">
                <span>{error instanceof ApiError ? error.message : "Something went wrong. Please try again."}</span>
                {canRetry && (
                  <Button variant="outline" size="sm" className="w-fit" onClick={retry}>
                    Retry
                  </Button>
                )}
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <ChatInput onSend={sendMessage} disabled={isSending} />
    </div>
  );
}

