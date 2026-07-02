"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ListVideo } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { AuditStatusChip } from "@/features/audits/components/audit-status-chip";
import { fetchAuditJobs } from "@/lib/api";
import { formatRelativeTime, shortId } from "@/lib/format";

export function RecentAuditsCard() {
  const { data: audits, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["audit-jobs"],
    queryFn: fetchAuditJobs,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Audits</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {isError && <ErrorState error={error} onRetry={() => refetch()} />}

        {!isError && isLoading &&
          Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-11 w-full" />)}

        {!isError && !isLoading && audits?.length === 0 && (
          <EmptyState icon={ListVideo} title="No audits yet" description="Submit a video to see it here." />
        )}

        {!isError && !isLoading &&
          audits?.slice(0, 5).map((audit) => {
            const row = (
              <div className="flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/50">
                <div className="min-w-0 space-y-0.5">
                  <p className="truncate text-sm font-medium text-foreground">{audit.video_id}</p>
                  <p className="font-technical text-xs text-muted-foreground">
                    {shortId(audit.id)} &middot; {formatRelativeTime(audit.created_at)}
                  </p>
                </div>
                <AuditStatusChip status={audit.status} />
              </div>
            );
            return audit.report_id ? (
              <Link key={audit.id} href={`/reports/${audit.report_id}`}>
                {row}
              </Link>
            ) : (
              <div key={audit.id}>{row}</div>
            );
          })}
      </CardContent>
    </Card>
  );
}
