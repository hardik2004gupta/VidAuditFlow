import { Badge } from "@/components/ui/badge";
import { FINAL_STATUS_CONFIG } from "@/lib/constants";
import type { FinalStatus } from "@/types/api";

export function FinalStatusBadge({ status, className }: { status: FinalStatus; className?: string }) {
  const config = FINAL_STATUS_CONFIG[status];
  return (
    <Badge variant="outline" className={`${config.badgeClassName} ${className ?? ""}`}>
      {config.label}
    </Badge>
  );
}
