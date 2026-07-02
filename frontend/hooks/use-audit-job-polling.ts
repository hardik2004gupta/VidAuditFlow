"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAuditJob } from "@/lib/api";
import { PIPELINE_STAGES, type AuditJob, type AuditJobStatus, type PipelineStageKey } from "@/types/api";

export type StageProgressState = "pending" | "active" | "done" | "error";

export interface StageProgress {
  key: PipelineStageKey;
  label: string;
  state: StageProgressState;
  /** Real per-stage timing isn't available while a job is still in flight --
   * `GET /api/v1/audits/{id}` only reports the current stage label, not a
   * start/end timestamp per stage (that detail only exists on the finished
   * Report's `processing_metadata`). Always null until the job is terminal. */
  elapsedSeconds: number | null;
}

const TERMINAL_STATUSES: ReadonlySet<AuditJobStatus> = new Set([
  "completed",
  "completed_degraded",
  "failed",
  "cancelled",
]);

function isTerminal(status: AuditJobStatus | undefined): boolean {
  return status != null && TERMINAL_STATUSES.has(status);
}

/**
 * Replaces the Phase 5 client-side timer simulation with real polling of
 * `GET /api/v1/audits/{id}` every 2 seconds (per API_PLAN.md's documented
 * "polling every 2-3s is a perfectly acceptable fallback" -- SSE is called
 * out there as an optional enhancement, not required). Stops polling the
 * moment the job reaches a terminal status.
 */
export function useAuditJobPolling(jobId: string | null) {
  const query = useQuery({
    queryKey: ["audit-job", jobId],
    queryFn: () => fetchAuditJob(jobId as string),
    enabled: jobId != null,
    refetchInterval: (q) => (isTerminal(q.state.data?.status) ? false : 2000),
  });

  const job = query.data;
  const currentIndex = job?.current_stage
    ? PIPELINE_STAGES.findIndex((stage) => stage.label === job.current_stage)
    : -1;

  const stages: StageProgress[] = PIPELINE_STAGES.map((stage, index) => {
    let state: StageProgressState = "pending";

    if (job?.status === "completed" || job?.status === "completed_degraded") {
      state = "done";
    } else if (job?.status === "failed" || job?.status === "cancelled") {
      state = index < currentIndex ? "done" : index === currentIndex ? "error" : "pending";
    } else if (index < currentIndex) {
      state = "done";
    } else if (index === currentIndex) {
      state = "active";
    }

    return { key: stage.key, label: stage.label, state, elapsedSeconds: null };
  });

  const isDoneSuccessfully = job?.status === "completed" || job?.status === "completed_degraded";
  const progressRatio = isDoneSuccessfully
    ? 1
    : Math.max(currentIndex, 0) / PIPELINE_STAGES.length;

  return {
    job: job as AuditJob | undefined,
    stages,
    progressRatio,
    isComplete: isTerminal(job?.status),
    isError: query.isError,
    error: query.error,
  };
}
