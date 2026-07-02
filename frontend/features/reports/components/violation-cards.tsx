"use client";

import { motion } from "framer-motion";
import { ChevronDown, ShieldCheck } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { EmptyState } from "@/components/shared/empty-state";
import { EvidenceCard } from "@/features/audits/components/evidence-card";
import { SeverityBadge } from "@/features/audits/components/severity-badge";
import { cn } from "@/lib/utils";
import type { ComplianceIssue } from "@/types/api";

interface ViolationCardsProps {
  violations: ComplianceIssue[];
}

/**
 * Premium, collapsible presentation of a report's violations -- replaces
 * the Phase 5/6 table + modal pattern. Each card's header (severity,
 * category, confidence, timestamp) is always visible; expanding it reveals
 * the same `EvidenceCard` detail body the Evidence Timeline uses, so the
 * "what does a violation's full detail look like" logic lives in one place.
 */
export function ViolationCards({ violations }: ViolationCardsProps) {
  if (violations.length === 0) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="No violations detected"
        description="This video passed compliance analysis with no flagged issues -- nothing to review here."
      />
    );
  }

  return (
    <div className="space-y-3">
      {violations.map((issue, index) => (
        <motion.div
          key={`${issue.category}-${index}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: index * 0.04 }}
        >
          <Collapsible className="rounded-lg border border-border bg-card transition-colors duration-150 hover:border-foreground/20">
            <CollapsibleTrigger className="group/violation flex w-full items-center gap-3 rounded-lg px-4 py-3.5 text-left outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <span
                className={cn(
                  "h-8 w-1 shrink-0 rounded-full",
                  issue.severity === "CRITICAL" ? "bg-critical" : "bg-warning",
                )}
                aria-hidden="true"
              />
              <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
                <SeverityBadge severity={issue.severity} />
                <span className="truncate text-sm font-medium text-foreground">{issue.category}</span>
              </div>
              <span className="font-technical shrink-0 text-xs tabular-nums text-muted-foreground">
                {Math.round(issue.confidence * 100)}%
              </span>
              {issue.timestamp && (
                <span className="font-technical hidden shrink-0 text-xs tabular-nums text-muted-foreground sm:inline">
                  {issue.timestamp}
                </span>
              )}
              <ChevronDown className="size-4 shrink-0 text-muted-foreground transition-transform duration-200 group-data-panel-open/violation:rotate-180" />
            </CollapsibleTrigger>
            <CollapsibleContent className="h-(--collapsible-panel-height) overflow-hidden transition-[height] duration-200 ease-out data-ending-style:h-0 data-starting-style:h-0">
              <div className="border-t border-border px-4 py-4">
                <EvidenceCard issue={issue} showHeader={false} />
              </div>
            </CollapsibleContent>
          </Collapsible>
        </motion.div>
      ))}
    </div>
  );
}
