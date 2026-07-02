import Link from "next/link";
import { ArrowRight, CheckCircle2, PartyPopper, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FinalStatusBadge } from "@/features/audits/components/final-status-badge";
import { SeverityBadge } from "@/features/audits/components/severity-badge";
import { extractMarkdownSection, parseMarkdownList } from "@/lib/markdown";
import { formatAbsoluteTime } from "@/lib/format";
import type { Report } from "@/types/api";

const TOP_FINDINGS_LIMIT = 3;

/**
 * The report's "letterhead" section -- executive summary, a condensed
 * preview of the top findings, and the recommended fixes, styled to read
 * like something an enterprise AI platform generated rather than a raw
 * pipeline dump. Compliance Score/Risk Level stay in their own gauge card
 * (ComplianceScoreCard) rather than being duplicated here.
 */
export function ExecutiveSummaryCard({ report }: { report: Report }) {
  const summary = extractMarkdownSection(report.final_report, "Executive Summary") || report.final_report;
  const fixesBlock = extractMarkdownSection(report.final_report, "Suggested Fixes");
  const fixes = parseMarkdownList(fixesBlock).filter((item) => item.toLowerCase() !== "none needed.");

  const topFindings = [...report.compliance_results]
    .sort((a, b) => {
      if (a.severity !== b.severity) return a.severity === "CRITICAL" ? -1 : 1;
      return b.confidence - a.confidence;
    })
    .slice(0, TOP_FINDINGS_LIMIT);

  return (
    <Card>
      <CardHeader className="flex items-start justify-between gap-3 space-y-0">
        <div className="flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="size-4 text-primary" aria-hidden="true" />
          </span>
          <div>
            <CardTitle>Executive Summary</CardTitle>
            <p className="text-xs text-muted-foreground">Generated {formatAbsoluteTime(report.created_at)}</p>
          </div>
        </div>
        <FinalStatusBadge status={report.final_status} />
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-[15px] leading-relaxed text-foreground/90">{summary}</p>

        <div className="space-y-3">
          <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Top Findings</p>
          {topFindings.length === 0 ? (
            <div className="flex items-center gap-2 rounded-lg border border-success/20 bg-success/5 px-3.5 py-3 text-sm text-foreground">
              <PartyPopper className="size-4 shrink-0 text-success" aria-hidden="true" />
              No violations detected -- this video is fully compliant.
            </div>
          ) : (
            <div className="space-y-1.5">
              {topFindings.map((issue, index) => (
                <div
                  key={`${issue.category}-${index}`}
                  className="flex items-center gap-2.5 rounded-lg border border-border px-3 py-2"
                >
                  <SeverityBadge severity={issue.severity} />
                  <span className="min-w-0 flex-1 truncate text-sm text-foreground">{issue.category}</span>
                  <span className="font-technical shrink-0 text-xs tabular-nums text-muted-foreground">
                    {Math.round(issue.confidence * 100)}%
                  </span>
                </div>
              ))}
              {report.compliance_results.length > TOP_FINDINGS_LIMIT && (
                <Link
                  href="#violations"
                  className="flex items-center gap-1 px-1 pt-1 text-xs font-medium text-primary hover:underline"
                >
                  View all {report.compliance_results.length} findings
                  <ArrowRight className="size-3" aria-hidden="true" />
                </Link>
              )}
            </div>
          )}
        </div>

        {fixes.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Recommendations</p>
            <ul className="space-y-2">
              {fixes.map((fix) => (
                <li key={fix} className="flex items-start gap-2 text-sm text-foreground/90">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
                  <span>{fix}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
