"use client";

import { motion } from "framer-motion";

/** Three-dot "the Copilot is thinking" indicator, shown while a reply is pending. */
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 rounded-lg bg-muted px-3 py-2.5" aria-label="AI Copilot is typing">
      {[0, 1, 2].map((index) => (
        <motion.span
          key={index}
          className="size-1.5 rounded-full bg-muted-foreground"
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
          transition={{ duration: 1, repeat: Infinity, delay: index * 0.15, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}
