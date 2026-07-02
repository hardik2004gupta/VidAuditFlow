"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { FinalStatusBadge } from "@/features/audits/components/final-status-badge";
import { fetchReports } from "@/lib/api";
import { formatRelativeTime } from "@/lib/format";

export function RecentReportsCard() {
  const { data: reports, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Reports</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {isError && <ErrorState error={error} onRetry={() => refetch()} />}

        {!isError && isLoading &&
          Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} className="h-11 w-full" />)}

        {!isError && !isLoading && reports?.length === 0 && (
          <EmptyState icon={FileText} title="No reports yet" description="Completed audits will appear here." />
        )}

        {!isError && !isLoading &&
          reports?.slice(0, 5).map((report) => (
            <Link
              key={report.id}
              href={`/reports/${report.id}`}
              className="flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/50"
            >
              <div className="min-w-0 space-y-0.5">
                <p className="truncate text-sm font-medium text-foreground">
                  Compliance Score: {report.confidence_score ?? "—"}
                </p>
                <p className="text-xs text-muted-foreground">{formatRelativeTime(report.created_at)}</p>
              </div>
              <FinalStatusBadge status={report.final_status} />
            </Link>
          ))}
      </CardContent>
    </Card>
  );
}
