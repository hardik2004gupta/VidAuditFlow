import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusChip } from "@/components/shared/status-chip";

const SYSTEMS = [
  { label: "AI Pipeline (LangGraph)" },
  { label: "Transcript Service" },
  { label: "OCR Service" },
  { label: "Policy Retrieval (RAG)" },
] as const;

/** Static, informational status list -- no real monitoring integration in this phase. */
export function SystemStatusCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {SYSTEMS.map((system) => (
          <div key={system.label} className="flex items-center justify-between gap-3">
            <span className="text-sm text-foreground">{system.label}</span>
            <StatusChip tone="success" label="Operational" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
