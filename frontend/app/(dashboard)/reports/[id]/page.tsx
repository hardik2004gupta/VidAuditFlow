import { notFound } from "next/navigation";
import { Clock, Video, Hash } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/shared/section-header";
import { ComplianceScoreCard } from "@/features/audits/components/compliance-score-card";
import { ViolationTable } from "@/features/audits/components/violation-table";
import { StageTimeline } from "@/features/audits/components/stage-timeline";
import { ExecutiveSummaryCard } from "@/features/reports/components/executive-summary-card";
import { SourcesPanel } from "@/features/reports/components/sources-panel";
import { WarningsBanner } from "@/features/reports/components/warnings-banner";
import { ApiError, fetchReport } from "@/lib/api";
import { formatDuration, shortId } from "@/lib/format";
import type { Report } from "@/types/api";

async function loadReport(id: string): Promise<Report> {
  try {
    return await fetchReport(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}

export default async function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = await loadReport(id);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Report ${shortId(report.id)}`}
        description="Full compliance breakdown for this audit."
        breadcrumb={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Reports", href: "/reports" },
          { label: shortId(report.id) },
        ]}
      />

      <WarningsBanner warnings={report.warnings} />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ExecutiveSummaryCard finalReport={report.final_report} />

          <div>
            <SectionHeader title="Violations" description={`${report.compliance_results.length} finding(s) detected`} />
            <ViolationTable violations={report.compliance_results} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Processing Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <StageTimeline traces={report.processing_metadata} />
            </CardContent>
          </Card>

          <SourcesPanel sources={report.sources} />
        </div>

        <div className="space-y-6">
          {report.confidence_score != null && report.risk_level && (
            <ComplianceScoreCard score={report.confidence_score} riskLevel={report.risk_level} />
          )}

          <Card>
            <CardHeader>
              <CardTitle>Video Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <Video className="size-4 text-muted-foreground" />
                <span className="capitalize text-foreground">{report.video_metadata.platform}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Clock className="size-4 text-muted-foreground" />
                <span className="text-foreground">{formatDuration(report.video_metadata.duration)}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Hash className="size-4 text-muted-foreground" />
                <span className="font-technical text-foreground">{shortId(report.audit_job_id)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
