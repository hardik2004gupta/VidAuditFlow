/**
 * Types mirroring the backend's Pydantic schemas exactly.
 *
 * Source of truth on the backend:
 *   - backend/src/schemas/jobs.py    (AuditJobRead, ReportRead, ReportSummary)
 *   - backend/src/schemas/audit.py   (ComplianceIssue, RetrievedRule)
 *   - backend/src/graph/observability.py (StageTrace)
 *   - backend/src/db/models.py       (AuditJobStatus)
 *
 * This phase does not call the real API (see PHASE_5_SUMMARY.md) -- these
 * types exist so the mock data layer (lib/mock/) and every component are
 * already shaped exactly like the real response bodies will be, per
 * API_PLAN.md. When backend integration lands, only `lib/api-client.ts`
 * needs to change; no component or type should need to.
 */

export type AuditJobStatus =
  | "queued"
  | "running"
  | "completed"
  | "completed_degraded"
  | "failed"
  | "cancelled";

export type Severity = "CRITICAL" | "WARNING";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export type FinalStatus = "PASS" | "FAIL";

export type StageStatus = "success" | "failed" | "skipped";

/** One compliance violation, exactly as produced by the Compliance Agent. */
export interface ComplianceIssue {
  category: string;
  severity: Severity;
  description: string;
  timestamp: string | null;
  /** 0.0-1.0 */
  confidence: number;
  evidence: string;
  policy_reference: string | null;
  recommendation: string;
}

/** One retrieved policy chunk, used for the Sources panel and citations. */
export interface RetrievedRule {
  content: string;
  source: string;
}

/** One node's execution record, from graph/observability.py. */
export interface StageTrace {
  node: string;
  status: StageStatus;
  started_at: string;
  ended_at: string;
  duration_seconds: number;
  error: string | null;
  tokens_used: number | null;
}

export interface VideoMetadata {
  duration: number | null;
  platform: string;
}

/** GET/POST /api/v1/audits response shape (AuditJobRead). */
export interface AuditJob {
  id: string;
  status: AuditJobStatus;
  current_stage: string | null;
  video_url: string;
  video_id: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  report_id: string | null;
}

/** GET /api/v1/reports/{id} response shape (ReportRead). */
export interface Report {
  id: string;
  audit_job_id: string;
  final_status: FinalStatus;
  confidence_score: number | null;
  risk_level: RiskLevel | null;
  created_at: string;
  final_report: string;
  compliance_results: ComplianceIssue[];
  video_metadata: VideoMetadata;
  processing_metadata: StageTrace[];
  warnings: string[];
  sources: RetrievedRule[];
}

/**
 * The seven real graph nodes and their human-readable stage labels, exactly
 * matching `backend/src/jobs/audit_runner.py`'s `_STAGE_LABELS` -- this is
 * the literal set of strings `AuditJob.current_stage` will contain, so the
 * live-tracker UI's step list is data-accurate, not just aspirational copy.
 */
export const PIPELINE_STAGES = [
  { key: "supervisor_start", label: "Starting Audit" },
  { key: "transcript_agent", label: "Downloading Video & Extracting Transcript" },
  { key: "ocr_agent", label: "Extracting OCR" },
  { key: "supervisor_join", label: "Validating Results" },
  { key: "retrieval_agent", label: "Retrieving Policies" },
  { key: "compliance_agent", label: "Compliance Analysis" },
  { key: "summary_agent", label: "Generating Summary" },
] as const;

export type PipelineStageKey = (typeof PIPELINE_STAGES)[number]["key"];
