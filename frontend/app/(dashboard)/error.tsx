"use client";

import { AlertTriangle, RotateCw } from "lucide-react";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

/** Route-level error boundary for every page under the dashboard shell. */
export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // In a real integration this would report to an error-tracking service.
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-critical/10">
        <AlertTriangle className="size-6 text-critical" />
      </div>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          This page hit an unexpected error. You can try again, or head back to the dashboard.
        </p>
      </div>
      <Button onClick={reset} variant="secondary" className="gap-2">
        <RotateCw className="size-4" />
        Try again
      </Button>
    </div>
  );
}
