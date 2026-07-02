import { Badge } from "@/components/ui/badge";
import { RISK_LEVEL_CONFIG } from "@/lib/constants";
import type { RiskLevel } from "@/types/api";

export function RiskBadge({ level, className }: { level: RiskLevel; className?: string }) {
  const config = RISK_LEVEL_CONFIG[level];
  return (
    <Badge variant="outline" className={`${config.badgeClassName} ${className ?? ""}`}>
      {config.label}
    </Badge>
  );
}
