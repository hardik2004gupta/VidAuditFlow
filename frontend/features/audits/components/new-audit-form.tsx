"use client";

import { useState } from "react";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { AlertTriangle, ArrowRight, CheckCircle2, Loader2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/shared/error-state";
import { StageTracker } from "@/features/audits/components/stage-tracker";
import { useAuditJobPolling } from "@/hooks/use-audit-job-polling";
import { createAudit } from "@/lib/api";

const YOUTUBE_URL_PATTERN = /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/i;

const auditFormSchema = z.object({
  videoUrl: z
    .string()
    .min(1, "A video URL is required.")
    .regex(YOUTUBE_URL_PATTERN, "Enter a valid YouTube video URL."),
});

type AuditFormValues = z.infer<typeof auditFormSchema>;

/**
 * The New Audit submission flow, wired to the real backend (Phase 6):
 * `POST /api/v1/audits` schedules the job, then `useAuditJobPolling` polls
 * `GET /api/v1/audits/{id}` every 2s and drives the same `StageTracker`
 * UI the Phase 5 simulation used -- only the data source changed.
 */
export function NewAuditForm() {
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AuditFormValues>({
    resolver: zodResolver(auditFormSchema),
    defaultValues: { videoUrl: "" },
  });

  const createMutation = useMutation({
    mutationFn: createAudit,
    onSuccess: (job) => {
      setJobId(job.id);
      queryClient.invalidateQueries({ queryKey: ["audit-jobs"] });
    },
  });

  const { job, stages, progressRatio, isComplete } = useAuditJobPolling(jobId);

  // Refresh the dashboard's audit/report lists once this job lands on a
  // report so "Recent Audits"/"Recent Reports" reflect it without a manual reload.
  const [hasRefreshedLists, setHasRefreshedLists] = useState(false);
  if (isComplete && job?.report_id && !hasRefreshedLists) {
    setHasRefreshedLists(true);
    queryClient.invalidateQueries({ queryKey: ["reports"] });
  }

  function onSubmit(values: AuditFormValues) {
    createMutation.mutate(values.videoUrl);
  }

  if (jobId) {
    return (
      <Card>
        <CardContent className="space-y-6 pt-2">
          <StageTracker stages={stages} progressRatio={progressRatio} />
          <AnimatePresence>
            {isComplete && (job?.status === "completed" || job?.status === "completed_degraded") && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, type: "spring", bounce: 0.4 }}
                className="flex flex-col items-center gap-3 rounded-lg border border-success/20 bg-success/5 px-6 py-8 text-center"
              >
                <CheckCircle2 className="size-8 text-success" />
                <p className="text-sm font-medium text-foreground">
                  {job.status === "completed_degraded" ? "Audit complete (degraded)" : "Audit complete"}
                </p>
                <p className="max-w-sm text-sm text-muted-foreground">
                  Your compliance report is ready with a full breakdown of every finding.
                </p>
                <Button render={<Link href={`/reports/${job.report_id}`} />}>
                  View Full Report
                  <ArrowRight className="size-4" data-icon="inline-end" />
                </Button>
              </motion.div>
            )}
            {isComplete && (job?.status === "failed" || job?.status === "cancelled") && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="flex flex-col items-center gap-3 rounded-lg border border-critical/20 bg-critical/5 px-6 py-8 text-center"
              >
                <AlertTriangle className="size-8 text-critical" />
                <p className="text-sm font-medium text-foreground">
                  {job.status === "cancelled" ? "Audit cancelled" : "Audit failed"}
                </p>
                <p className="max-w-sm text-sm text-muted-foreground">
                  {job.error_message ?? "The pipeline could not complete this audit."}
                </p>
                <Button variant="outline" onClick={() => setJobId(null)}>
                  Start a new audit
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="pt-2">
        {createMutation.isError && (
          <div className="mb-4">
            <ErrorState error={createMutation.error} title="Couldn't start this audit" />
          </div>
        )}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="videoUrl">YouTube video URL</Label>
            <Input
              id="videoUrl"
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              aria-invalid={!!errors.videoUrl}
              aria-describedby={errors.videoUrl ? "videoUrl-error" : undefined}
              {...register("videoUrl")}
            />
            {errors.videoUrl && (
              <p id="videoUrl-error" className="text-xs text-destructive" role="alert">
                {errors.videoUrl.message}
              </p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={createMutation.isPending}>
            {createMutation.isPending ? (
              <>
                <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
                Starting audit…
              </>
            ) : (
              <>
                Analyze video
                <ArrowRight className="size-4" data-icon="inline-end" />
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
