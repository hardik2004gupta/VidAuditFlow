"use client";

import { motion } from "framer-motion";
import { CheckCircle2, XCircle, MinusCircle, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatStageDuration } from "@/lib/format";
import { PIPELINE_STAGES } from "@/types/api";
import type { StageTrace, StageStatus } from "@/types/api";

const STATUS_ICON: Record<StageStatus, typeof CheckCircle2> = {
  success: CheckCircle2,
  failed: XCircle,
  skipped: MinusCircle,
};

const STATUS_CLASSES: Record<StageStatus, string> = {
  success: "text-success",
  failed: "text-critical",
  skipped: "text-muted-foreground",
};

function stageLabel(node: string): string {
  return PIPELINE_STAGES.find((stage) => stage.key === node)?.label ?? node;
}

/** Renders a Report's `processing_metadata` as a vertical execution timeline. */
export function StageTimeline({ traces }: { traces: StageTrace[] }) {
  return (
    <ol className="space-y-1">
      {traces.map((trace, index) => {
        const Icon = STATUS_ICON[trace.status];
        const isLast = index === traces.length - 1;
        return (
          <motion.li
            key={trace.node}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: index * 0.05 }}
            className="relative flex gap-3 pb-4"
          >
            {!isLast && (
              <span
                className="absolute top-6 left-[11px] h-full w-px bg-border"
                aria-hidden="true"
              />
            )}
            <Icon className={cn("mt-0.5 size-[22px] shrink-0", STATUS_CLASSES[trace.status])} />
            <div className="flex-1 space-y-0.5 pb-1">
              <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                <p className="text-sm font-medium text-foreground">{stageLabel(trace.node)}</p>
                <span className="font-technical text-xs tabular-nums text-muted-foreground">
                  {formatStageDuration(trace.duration_seconds)}
                </span>
              </div>
              {trace.error && <p className="text-xs text-critical">{trace.error}</p>}
              {trace.tokens_used != null && (
                <p className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Zap className="size-3" aria-hidden="true" />
                  {trace.tokens_used.toLocaleString()} tokens
                </p>
              )}
            </div>
          </motion.li>
        );
      })}
    </ol>
  );
}
