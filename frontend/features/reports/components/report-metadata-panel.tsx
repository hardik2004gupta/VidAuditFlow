import type { LucideIcon } from "lucide-react";
import { AlertTriangle, BookText, CalendarCheck, Clock, Cpu, GitBranch, Hash, ShieldCheck, Video } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FinalStatusBadge } from "@/features/audits/components/final-status-badge";
import { computeProcessingSpanSeconds, formatAbsoluteTime, formatDuration, formatStageDuration, shortId } from "@/lib/format";
import type { Report } from "@/types/api";

function MetaRow({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="flex items-center gap-2 text-muted-foreground">
        <Icon className="size-4 shrink-0" aria-hidden="true" />
        {label}
      </span>
      <span className="min-w-0 truncate text-right font-medium text-foreground">{value}</span>
    </div>
  );
}

/**
 * Report Details sidebar panel (Part 4): every field here comes straight
 * from the existing `ReportRead` response -- no new backend fields. "Model"
 * and "Pipeline Version" are the two exceptions: the API doesn't expose a
 * per-report model/version field, so these describe the fixed, publicly
 * documented pipeline architecture (see the landing page's own Architecture
 * section) rather than fabricated dynamic data.
 */
export function ReportMetadataPanel({ report }: { report: Report }) {
  const processingSeconds = computeProcessingSpanSeconds(report.processing_metadata);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Report Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <MetaRow icon={Video} label="Platform" value={report.video_metadata.platform || "—"} />
        <MetaRow icon={Clock} label="Video Duration" value={formatDuration(report.video_metadata.duration)} />
        <MetaRow
          icon={Hash}
          label="Audit Job"
          value={<span className="font-technical">{shortId(report.audit_job_id)}</span>}
        />

        <div className="my-1 h-px bg-border" aria-hidden="true" />

        <MetaRow icon={CalendarCheck} label="Completed" value={formatAbsoluteTime(report.created_at)} />
        <MetaRow
          icon={Clock}
          label="Processing Time"
          value={processingSeconds != null ? formatStageDuration(processingSeconds) : "—"}
        />
        <MetaRow icon={Cpu} label="Model" value="Azure OpenAI" />
        <MetaRow icon={GitBranch} label="Pipeline" value="Supervisor · 7-stage" />
        <div className="flex items-center justify-between gap-3 text-sm">
          <span className="flex items-center gap-2 text-muted-foreground">
            <ShieldCheck className="size-4 shrink-0" aria-hidden="true" />
            Status
          </span>
          <FinalStatusBadge status={report.final_status} />
        </div>

        <div className="my-1 h-px bg-border" aria-hidden="true" />

        <MetaRow
          icon={AlertTriangle}
          label="Warnings"
          value={report.warnings.length > 0 ? report.warnings.length : "None"}
        />
        <MetaRow icon={BookText} label="Sources" value={report.sources.length} />
      </CardContent>
    </Card>
  );
}

