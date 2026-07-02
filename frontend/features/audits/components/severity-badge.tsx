import { Badge } from "@/components/ui/badge";
import { SEVERITY_CONFIG } from "@/lib/constants";
import type { Severity } from "@/types/api";

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  const config = SEVERITY_CONFIG[severity];
  return (
    <Badge variant="outline" className={`${config.badgeClassName} ${className ?? ""}`}>
      {config.label}
    </Badge>
  );
}
