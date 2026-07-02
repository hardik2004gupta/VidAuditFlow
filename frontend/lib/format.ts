import { formatDistanceToNow } from "date-fns";

/** "2h ago", "3d ago" -- used across audit history, report timestamps. */
export function formatRelativeTime(iso: string): string {
  return formatDistanceToNow(new Date(iso), { addSuffix: true });
}

/** "Jun 28, 2026, 2:19 PM" -- used on the report detail page. */
export function formatAbsoluteTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** Seconds -> "10:12" for video duration / evidence timestamps. */
export function formatDuration(totalSeconds: number | null | undefined): string {
  if (totalSeconds == null) return "—";
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/** Duration in seconds -> "2m 47s" / "820ms" for stage-timing display. */
export function formatStageDuration(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.round(seconds % 60);
  return `${minutes}m ${remaining}s`;
}

/** Extracts a short, stable display id from a UUID, e.g. "b3f1a9c2". */
export function shortId(id: string): string {
  return id.replace(/-/g, "").slice(0, 8);
}

/**
 * Parses a violation's "mm:ss" (or "h:mm:ss") timestamp into seconds, for
 * chronological sorting. Returns `null` unparseable/missing so callers can
 * push undated violations to the end instead of guessing a position.
 */
export function parseTimestampToSeconds(timestamp: string | null): number | null {
  if (!timestamp) return null;
  const parts = timestamp.split(":").map(Number);
  if (parts.some((part) => Number.isNaN(part))) return null;
  return parts.reduceRight((total, part, index) => total + part * Math.pow(60, parts.length - 1 - index), 0);
}

/**
 * Total wall-clock span of a report's `processing_metadata` (earliest
 * stage start to latest stage end) -- a reasonable "processing time" figure
 * since the Report response has no single duration field of its own.
 */
export function computeProcessingSpanSeconds(
  traces: { started_at: string; ended_at: string }[],
): number | null {
  if (traces.length === 0) return null;
  const starts = traces.map((t) => new Date(t.started_at).getTime());
  const ends = traces.map((t) => new Date(t.ended_at).getTime());
  return (Math.max(...ends) - Math.min(...starts)) / 1000;
}
