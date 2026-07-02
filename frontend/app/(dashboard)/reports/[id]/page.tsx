import { notFound } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { SectionHeader } from "@/components/shared/section-header";
import { ComplianceScoreCard } from "@/features/audits/components/compliance-score-card";
import { ExecutiveSummaryCard } from "@/features/reports/components/executive-summary-card";
import { EvidenceTimeline } from "@/features/reports/components/evidence-timeline";
import { ReportActionsMenu } from "@/features/reports/components/report-actions-menu";
import { ReportMetadataPanel } from "@/features/reports/components/report-metadata-panel";
import { SourcesPanel } from "@/features/reports/components/sources-panel";
import { ViolationCards } from "@/features/reports/components/violation-cards";
import { WarningsBanner } from "@/features/reports/components/warnings-banner";
import { ApiError, fetchReport } from "@/lib/api";
import { shortId } from "@/lib/format";
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
        action={<ReportActionsMenu report={report} />}
      />

      <WarningsBanner warnings={report.warnings} />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ExecutiveSummaryCard report={report} />

          <div id="violations">
            <SectionHeader
              title="Violations"
              description={`${report.compliance_results.length} finding(s) detected`}
            />
            <ViolationCards violations={report.compliance_results} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Evidence Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <EvidenceTimeline violations={report.compliance_results} />
            </CardContent>
          </Card>

          <SourcesPanel sources={report.sources} />
        </div>

        <div className="space-y-6">
          {report.confidence_score != null && report.risk_level && (
            <ComplianceScoreCard score={report.confidence_score} riskLevel={report.risk_level} />
          )}

          <ReportMetadataPanel report={report} />
        </div>
      </div>
    </div>
  );
}
