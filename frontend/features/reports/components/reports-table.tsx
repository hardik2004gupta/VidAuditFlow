"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { FileText, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { FinalStatusBadge } from "@/features/audits/components/final-status-badge";
import { RiskBadge } from "@/features/audits/components/risk-badge";
import { fetchAuditJobs, fetchReports } from "@/lib/api";
import { formatAbsoluteTime } from "@/lib/format";

export function ReportsTable() {
  const router = useRouter();
  const {
    data: reports,
    isLoading: reportsLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });
  const { data: audits } = useQuery({ queryKey: ["audit-jobs"], queryFn: fetchAuditJobs });

  if (isError) {
    return <ErrorState error={error} onRetry={() => refetch()} title="Couldn't load reports" />;
  }

  if (reportsLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!reports || reports.length === 0) {
    return <EmptyState icon={FileText} title="No reports yet" description="Completed audits will appear here." />;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Video</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Risk</TableHead>
            <TableHead className="text-right">Score</TableHead>
            <TableHead className="hidden md:table-cell">Created</TableHead>
            <TableHead className="w-10" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {reports.map((report) => {
            const audit = audits?.find((a) => a.id === report.audit_job_id);
            return (
              <TableRow key={report.id} className="cursor-pointer" onClick={() => router.push(`/reports/${report.id}`)}>
                <TableCell className="font-medium text-foreground">
                  {audit?.video_id ?? report.audit_job_id.slice(0, 8)}
                </TableCell>
                <TableCell>
                  <FinalStatusBadge status={report.final_status} />
                </TableCell>
                <TableCell>{report.risk_level && <RiskBadge level={report.risk_level} />}</TableCell>
                <TableCell className="text-right font-technical tabular-nums text-muted-foreground">
                  {report.confidence_score ?? "—"}
                </TableCell>
                <TableCell className="hidden text-muted-foreground md:table-cell">
                  {formatAbsoluteTime(report.created_at)}
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon-sm" aria-label="View report" render={<Link href={`/reports/${report.id}`} />}>
                    <Eye className="size-4" />
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
