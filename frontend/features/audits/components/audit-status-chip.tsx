import { StatusChip, type StatusTone } from "@/components/shared/status-chip";
import { AUDIT_STATUS_CONFIG } from "@/lib/constants";
import type { AuditJobStatus } from "@/types/api";

const STATUS_TONE: Record<AuditJobStatus, StatusTone> = {
  queued: "muted",
  running: "info",
  completed: "success",
  completed_degraded: "warning",
  failed: "critical",
  cancelled: "muted",
};

export function AuditStatusChip({ status }: { status: AuditJobStatus }) {
  return (
    <StatusChip
      tone={STATUS_TONE[status]}
      label={AUDIT_STATUS_CONFIG[status].label}
      pulse={status === "running"}
    />
  );
}
