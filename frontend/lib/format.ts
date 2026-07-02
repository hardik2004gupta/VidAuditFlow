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
