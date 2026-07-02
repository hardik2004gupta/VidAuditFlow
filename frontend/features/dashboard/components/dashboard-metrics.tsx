"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, CheckCircle2, Gauge, Loader2 } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import { ErrorState } from "@/components/shared/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchAuditJobs, fetchReports } from "@/lib/api";

export function DashboardMetrics() {
  const {
    data: audits,
    isLoading: auditsLoading,
    isError: auditsError,
    error: auditsErrorObj,
    refetch: refetchAudits,
  } = useQuery({
    queryKey: ["audit-jobs"],
    queryFn: fetchAuditJobs,
  });
  const { data: reports, isLoading: reportsLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  if (auditsError) {
    return <ErrorState error={auditsErrorObj} onRetry={() => refetchAudits()} title="Couldn't load metrics" />;
  }

  if (auditsLoading || reportsLoading || !audits || !reports) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-[92px] w-full rounded-lg" />
        ))}
      </div>
    );
  }

  const activeCount = audits.filter((a) => a.status === "running" || a.status === "queued").length;
  const passCount = reports.filter((r) => r.final_status === "PASS").length;
  const passRate = reports.length > 0 ? Math.round((passCount / reports.length) * 100) : 0;
  const scored = reports.filter((r) => r.confidence_score != null);
  const avgConfidence =
    scored.length > 0
      ? Math.round(scored.reduce((sum, r) => sum + (r.confidence_score ?? 0), 0) / scored.length)
      : 0;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard label="Total Audits" value={String(audits.length)} icon={Activity} />
      <MetricCard label="Active Jobs" value={String(activeCount)} icon={Loader2} tone="default" />
      <MetricCard
        label="Pass Rate"
        value={`${passRate}%`}
        icon={CheckCircle2}
        tone={passRate >= 70 ? "success" : passRate >= 40 ? "warning" : "critical"}
      />
      <MetricCard label="Avg. Confidence" value={`${avgConfidence}/100`} icon={Gauge} />
    </div>
  );
}
