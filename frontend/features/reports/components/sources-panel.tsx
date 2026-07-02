import { BookText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import type { RetrievedRule } from "@/types/api";

export function SourcesPanel({ sources }: { sources: RetrievedRule[] }) {
  return (
    <Card>
      <CardHeader className="flex items-center justify-between gap-3 space-y-0">
        <CardTitle>Sources</CardTitle>
        {sources.length > 0 && (
          <span className="font-technical text-xs text-muted-foreground">
            {sources.length} policy {sources.length === 1 ? "excerpt" : "excerpts"}
          </span>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {sources.length === 0 && (
          <EmptyState
            icon={BookText}
            title="No policy sources retrieved"
            description="The retrieval stage didn't surface any policy passages for this video -- findings below aren't backed by a citation."
          />
        )}
        {sources.map((rule, index) => (
          <div
            key={index}
            className="rounded-lg border border-border p-3 transition-colors duration-150 hover:border-foreground/20"
          >
            <p className="text-sm text-foreground/90">{rule.content}</p>
            <p className="mt-2 font-technical text-xs text-muted-foreground">{rule.source}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
