"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Bot, Check, Copy, User } from "lucide-react";
import { MarkdownRenderer } from "@/features/reports/components/copilot/markdown-renderer";
import { cn } from "@/lib/utils";
import type { ChatTurn } from "@/types/api";

/** One conversation turn -- user bubbles right-aligned/accent, assistant left-aligned with Markdown + a hover-revealed copy button. */
export function ChatMessage({ turn }: { turn: ChatTurn }) {
  const [copied, setCopied] = useState(false);
  const isUser = turn.role === "user";

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(turn.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard write blocked -- copy is a convenience here, not critical.
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn("group/message flex gap-2", isUser && "flex-row-reverse")}
    >
      <span
        className={cn(
          "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground",
        )}
        aria-hidden="true"
      >
        {isUser ? <User className="size-3.5" /> : <Bot className="size-3.5" />}
      </span>

      <div className="flex max-w-[85%] flex-col gap-1">
        <div
          className={cn(
            "rounded-lg px-3 py-2",
            isUser
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : "rounded-tl-sm border border-border bg-card text-foreground",
          )}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{turn.content}</p>
          ) : (
            <MarkdownRenderer content={turn.content} />
          )}
        </div>
        <button
          type="button"
          onClick={handleCopy}
          aria-label="Copy message"
          className={cn(
            "flex w-fit items-center gap-1 rounded px-1 text-[11px] text-muted-foreground opacity-0 transition-opacity hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none group-hover/message:opacity-100",
            isUser && "self-end",
          )}
        >
          {copied ? (
            <>
              <Check className="size-3 text-success" /> Copied
            </>
          ) : (
            <>
              <Copy className="size-3" /> Copy
            </>
          )}
        </button>
      </div>
    </motion.div>
  );
}
