import { extractMarkdownSection, parseMarkdownList } from "@/lib/markdown";
import type { Report } from "@/types/api";

/** Plain-text executive summary, suitable for pasting into an email/ticket. */
export function buildSummaryText(report: Report): string {
  const summary = extractMarkdownSection(report.final_report, "Executive Summary") || report.final_report;
  return [
    `VidAuditFlow Report ${report.id}`,
    `Status: ${report.final_status}${report.risk_level ? ` (${report.risk_level} risk)` : ""}`,
    report.confidence_score != null ? `Compliance score: ${report.confidence_score}/100` : null,
    "",
    summary,
  ]
    .filter((line): line is string => line != null)
    .join("\n");
}

/** Numbered recommendations list, pulled from the report's "Suggested Fixes" section. */
export function buildRecommendationsText(report: Report): string {
  const block = extractMarkdownSection(report.final_report, "Suggested Fixes");
  const fixes = parseMarkdownList(block).filter((item) => item.toLowerCase() !== "none needed.");
  if (fixes.length === 0) return "No recommendations -- no violations were flagged.";
  return fixes.map((fix, index) => `${index + 1}. ${fix}`).join("\n");
}

/** Full evidence dossier: every violation's quote, policy, and recommendation. */
export function buildEvidenceText(report: Report): string {
  if (report.compliance_results.length === 0) {
    return "No violations were detected in this audit.";
  }
  return report.compliance_results
    .map((issue, index) => {
      const lines = [
        `${index + 1}. [${issue.severity}] ${issue.category}${issue.timestamp ? ` (${issue.timestamp})` : ""}`,
        `   Confidence: ${Math.round(issue.confidence * 100)}%`,
        `   Evidence: ${issue.evidence}`,
        `   Policy: ${issue.policy_reference ?? "—"}`,
        `   Recommendation: ${issue.recommendation}`,
      ];
      return lines.join("\n");
    })
    .join("\n\n");
}

/** Triggers a browser download of the raw report JSON. */
export function downloadReportJson(report: Report): void {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `vidauditflow-report-${report.id.slice(0, 8)}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
