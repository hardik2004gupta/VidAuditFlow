import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { extractMarkdownSection, parseMarkdownList } from "@/lib/markdown";

export function ExecutiveSummaryCard({ finalReport }: { finalReport: string }) {
  const summary = extractMarkdownSection(finalReport, "Executive Summary");
  const fixesBlock = extractMarkdownSection(finalReport, "Suggested Fixes");
  const fixes = parseMarkdownList(fixesBlock).filter((item) => item.toLowerCase() !== "none needed.");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Executive Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed text-foreground/90">{summary}</p>
        {fixes.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Suggested Fixes
            </p>
            <ul className="list-inside list-disc space-y-1.5 text-sm text-foreground/90">
              {fixes.map((fix) => (
                <li key={fix}>{fix}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
