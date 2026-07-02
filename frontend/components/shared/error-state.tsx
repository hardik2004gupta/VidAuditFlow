"use client";

import { AlertTriangle, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  title?: string;
}

/** Inline error treatment for a failed TanStack Query fetch -- the query-level counterpart to EmptyState. */
export function ErrorState({ error, onRetry, title = "Couldn't load this data" }: ErrorStateProps) {
  const message = error instanceof ApiError ? error.message : "An unexpected error occurred.";

  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-critical/30 bg-critical/5 px-6 py-14 text-center">
      <div className="flex size-11 items-center justify-center rounded-full bg-critical/10">
        <AlertTriangle className="size-5 text-critical" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="max-w-sm text-sm text-muted-foreground">{message}</p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RotateCw className="size-3.5" data-icon="inline-start" />
          Try again
        </Button>
      )}
    </div>
  );
}
