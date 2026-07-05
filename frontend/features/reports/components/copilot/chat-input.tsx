"use client";

import { useState, type KeyboardEvent } from "react";
import { ArrowUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

/** Enter sends, Shift+Enter inserts a newline -- the universal chat-input convention. */
export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  function submit() {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="flex items-end gap-2 border-t border-border p-3">
      <Textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about this report..."
        aria-label="Message the AI Copilot"
        disabled={disabled}
        className="max-h-32 min-h-9 resize-none border-none bg-muted px-3 py-2 text-sm shadow-none focus-visible:ring-1"
        rows={1}
      />
      <Button
        type="button"
        size="icon"
        aria-label="Send message"
        disabled={disabled || !value.trim()}
        onClick={submit}
      >
        <ArrowUp className="size-4" />
      </Button>
    </div>
  );
}
