import type { LucideIcon } from "lucide-react";

interface SuggestedPromptProps {
  icon: LucideIcon;
  label: string;
  onSelect: () => void;
}

/** A tappable suggested-question pill, shown in the Copilot's empty state. */
export function SuggestedPrompt({ icon: Icon, label, onSelect }: SuggestedPromptProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className="flex w-full items-center gap-2.5 rounded-lg border border-border bg-card px-3 py-2.5 text-left text-sm text-foreground transition-colors duration-150 hover:border-primary/40 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <Icon className="size-4 shrink-0 text-primary" aria-hidden="true" />
      {label}
    </button>
  );
}
