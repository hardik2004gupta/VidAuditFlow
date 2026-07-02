"use client";

import { motion } from "framer-motion";
import { ChevronDown, Clock3 } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { EmptyState } from "@/components/shared/empty-state";
import { EvidenceCard } from "@/features/audits/components/evidence-card";
import { SeverityBadge } from "@/features/audits/components/severity-badge";
import { cn } from "@/lib/utils";
import { parseTimestampToSeconds } from "@/lib/format";
import type { ComplianceIssue } from "@/types/api";

interface EvidenceTimelineProps {
  violations: ComplianceIssue[];
}

/**
 * Chronological (by in-video timestamp) view of a report's violations --
 * replaces the Phase 5/6 pipeline "Processing Timeline" (which plotted
 * *how the audit ran*, not *where in the video the findings are*, and now
 * lives instead as the "Processing Time" figure in ReportMetadataPanel).
 * Undated violations sort to the end rather than being guessed at.
 */
export function EvidenceTimeline({ violations }: EvidenceTimelineProps) {
  if (violations.length === 0) {
    return (
      <EmptyState
        icon={Clock3}
        title="Nothing to plot on a timeline"
        description="No violations were detected, so there's no evidence to place in time."
      />
    );
  }

  const sorted = [...violations]
    .map((issue, originalIndex) => ({ issue, originalIndex, seconds: parseTimestampToSeconds(issue.timestamp) }))
    .sort((a, b) => {
      if (a.seconds == null && b.seconds == null) return a.originalIndex - b.originalIndex;
      if (a.seconds == null) return 1;
      if (b.seconds == null) return -1;
      return a.seconds - b.seconds;
    });

  return (
    <ol className="space-y-0">
      {sorted.map(({ issue, originalIndex }, index) => {
        const isLast = index === sorted.length - 1;
        return (
          <motion.li
            key={`${issue.category}-${originalIndex}`}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25, delay: index * 0.05 }}
            className="relative flex gap-3 pb-3"
          >
            {!isLast && (
              <span className="absolute top-8 left-[9px] h-full w-px bg-border" aria-hidden="true" />
            )}
            <span
              className={cn(
                "mt-2.5 flex size-[18px] shrink-0 items-center justify-center rounded-full ring-4 ring-background",
                issue.severity === "CRITICAL" ? "bg-critical" : "bg-warning",
              )}
              aria-hidden="true"
            />
            <Collapsible className="flex-1 rounded-lg border border-border bg-card transition-colors duration-150 hover:border-foreground/20">
              <CollapsibleTrigger className="group/timeline flex w-full items-center gap-2.5 rounded-lg px-3.5 py-3 text-left outline-none focus-visible:ring-2 focus-visible:ring-ring">
                <span className="font-technical shrink-0 text-xs font-medium tabular-nums text-foreground">
                  {issue.timestamp ?? "—:—"}
                </span>
                <SeverityBadge severity={issue.severity} />
                <span className="min-w-0 flex-1 truncate text-sm text-foreground">{issue.category}</span>
                <span className="font-technical shrink-0 text-xs tabular-nums text-muted-foreground">
                  {Math.round(issue.confidence * 100)}%
                </span>
                <ChevronDown className="size-4 shrink-0 text-muted-foreground transition-transform duration-200 group-data-panel-open/timeline:rotate-180" />
              </CollapsibleTrigger>
              <CollapsibleContent className="h-(--collapsible-panel-height) overflow-hidden transition-[height] duration-200 ease-out data-ending-style:h-0 data-starting-style:h-0">
                <div className="border-t border-border px-3.5 py-3.5">
                  <EvidenceCard issue={issue} showHeader={false} />
                </div>
              </CollapsibleContent>
            </Collapsible>
          </motion.li>
        );
      })}
    </ol>
  );
}
