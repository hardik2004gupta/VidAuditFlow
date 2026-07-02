import { BookText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import type { RetrievedRule } from "@/types/api";

export function SourcesPanel({ sources }: { sources: RetrievedRule[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Sources</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {sources.length === 0 && (
          <EmptyState icon={BookText} title="No policy sources retrieved" />
        )}
        {sources.map((rule, index) => (
          <div key={index} className="rounded-lg border border-border p-3">
            <p className="text-sm text-foreground/90">{rule.content}</p>
            <p className="mt-2 font-technical text-xs text-muted-foreground">{rule.source}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
