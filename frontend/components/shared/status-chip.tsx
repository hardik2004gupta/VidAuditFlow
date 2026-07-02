import { cn } from "@/lib/utils";

export type StatusTone = "success" | "warning" | "critical" | "info" | "muted";

const TONE_CLASSES: Record<StatusTone, string> = {
  success: "bg-success/10 text-success border-success/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  critical: "bg-critical/10 text-critical border-critical/20",
  info: "bg-info/10 text-info border-info/20",
  muted: "bg-muted text-muted-foreground border-border",
};

const DOT_CLASSES: Record<StatusTone, string> = {
  success: "bg-success",
  warning: "bg-warning",
  critical: "bg-critical",
  info: "bg-info",
  muted: "bg-muted-foreground",
};

interface StatusChipProps {
  tone: StatusTone;
  label: string;
  /** Animate the dot (e.g. a "live"/in-progress state) -- used sparingly. */
  pulse?: boolean;
  className?: string;
}

/**
 * A small dot-led status pill, distinct from `Badge`: StatusChip exists
 * specifically to signal *liveness* (an animated dot for in-progress
 * states), whereas static severity/verdict badges use `Badge` directly
 * with the tone classNames from `lib/constants.ts`.
 */
export function StatusChip({ tone, label, pulse = false, className }: StatusChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        TONE_CLASSES[tone],
        className,
      )}
    >
      <span className="relative flex size-1.5">
        {pulse && (
          <span
            className={cn(
              "absolute inline-flex size-full animate-ping rounded-full opacity-75 motion-reduce:animate-none",
              DOT_CLASSES[tone],
            )}
          />
        )}
        <span className={cn("relative inline-flex size-1.5 rounded-full", DOT_CLASSES[tone])} />
      </span>
      {label}
    </span>
  );
}
