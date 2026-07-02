import { Quote, FileText, Lightbulb, Clock } from "lucide-react";
import { SeverityBadge } from "@/features/audits/components/severity-badge";
import type { ComplianceIssue } from "@/types/api";

interface EvidenceCardProps {
  issue: ComplianceIssue;
  /** Hide the severity/category/timestamp row -- set to false when the
   * caller (e.g. a card or timeline entry) already renders that header
   * itself, so it isn't shown twice. */
  showHeader?: boolean;
}

/**
 * Full detail for a single violation -- evidence quote, confidence,
 * policy reference, and recommendation. The single shared source of truth
 * for "what does one violation's full detail look like," reused by
 * ViolationCards and EvidenceTimeline instead of each re-implementing it.
 */
export function EvidenceCard({ issue, showHeader = true }: EvidenceCardProps) {
  return (
    <div className="space-y-4">
      {showHeader && (
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={issue.severity} />
          <span className="text-sm font-medium text-foreground">{issue.category}</span>
          {issue.timestamp && (
            <span className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="size-3.5" aria-hidden="true" />
              {issue.timestamp}
            </span>
          )}
        </div>
      )}

      <p className="text-sm text-foreground">{issue.description}</p>

      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <Quote className="size-3.5" aria-hidden="true" />
          Evidence
        </div>
        <p className="font-technical text-sm text-foreground/90">{issue.evidence}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-border p-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Lightbulb className="size-3.5" aria-hidden="true" />
            Recommendation
          </div>
          <p className="text-sm text-foreground/90">{issue.recommendation}</p>
        </div>
        <div className="rounded-lg border border-border p-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <FileText className="size-3.5" aria-hidden="true" />
            Policy Reference
          </div>
          <p className="text-sm text-foreground/90">{issue.policy_reference ?? "—"}</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Model confidence</span>
        <span className="font-technical tabular-nums">{Math.round(issue.confidence * 100)}%</span>
      </div>
    </div>
  );
}
