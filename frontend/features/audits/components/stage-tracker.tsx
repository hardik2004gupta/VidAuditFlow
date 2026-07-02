"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, CircleDashed, LoaderCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import type { StageProgress } from "@/hooks/use-audit-job-polling";

interface StageTrackerProps {
  stages: StageProgress[];
  progressRatio: number;
}

/**
 * The live vertical audit stepper -- UI_VISION.md's "Live Audit Tracker"
 * signature screen. Pure/presentational: driven by whatever progress state
 * `useAuditJobPolling` hands it.
 */
export function StageTracker({ stages, progressRatio }: StageTrackerProps) {
  return (
    <div className="space-y-6">
      <Progress value={Math.round(progressRatio * 100)} />
      <ol className="space-y-0">
        {stages.map((stage, index) => {
          const isLast = index === stages.length - 1;
          return (
            <li key={stage.key} className="relative flex gap-3 pb-6">
              {!isLast && (
                <span
                  className={cn(
                    "absolute top-6 left-[11px] h-full w-px transition-colors duration-300",
                    stage.state === "done" && "bg-success/40",
                    stage.state === "error" && "bg-critical/40",
                    stage.state !== "done" && stage.state !== "error" && "bg-border",
                  )}
                  aria-hidden="true"
                />
              )}
              <span className="mt-0.5 flex size-[22px] shrink-0 items-center justify-center">
                <AnimatePresence mode="wait" initial={false}>
                  {stage.state === "done" && (
                    <motion.span
                      key="done"
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.5, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <CheckCircle2 className="size-[22px] text-success" />
                    </motion.span>
                  )}
                  {stage.state === "active" && (
                    <motion.span
                      key="active"
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.5, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <LoaderCircle className="size-[22px] animate-spin text-primary motion-reduce:animate-none" />
                    </motion.span>
                  )}
                  {stage.state === "pending" && (
                    <motion.span
                      key="pending"
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.5, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <CircleDashed className="size-[22px] text-muted-foreground/50" />
                    </motion.span>
                  )}
                  {stage.state === "error" && (
                    <motion.span
                      key="error"
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.5, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <XCircle className="size-[22px] text-critical" />
                    </motion.span>
                  )}
                </AnimatePresence>
              </span>
              <div className="flex flex-1 items-center justify-between gap-3">
                <p
                  className={cn(
                    "text-sm transition-colors",
                    stage.state === "pending"
                      ? "text-muted-foreground"
                      : "font-medium text-foreground",
                  )}
                >
                  {stage.label}
                </p>
                {stage.elapsedSeconds != null && (
                  <span className="font-technical text-xs tabular-nums text-muted-foreground">
                    {stage.elapsedSeconds.toFixed(1)}s
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
