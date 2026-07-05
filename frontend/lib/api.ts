import type { AuditJob, ChatMessageResponse, ChatTurn, Report } from "@/types/api";

/**
 * Real API client for the FastAPI backend (Phase 6). Replaces `lib/mock/`
 * entirely -- every function here has the exact same name/signature the
 * mock layer used, so no calling component needed to change shape, only
 * the import path.
 *
 * Base URL: `NEXT_PUBLIC_API_URL` (see `.env.example`), defaulting to the
 * local backend's default port so `npm run dev` works with zero setup
 * when the backend is also running locally.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/**
 * Extracts a human-readable message from either of the backend's two error
 * shapes: the app's own `{"error": {"code", "message"}}` envelope (see
 * `api/main.py`'s exception handlers), or FastAPI's default Pydantic `422`
 * shape (`{"detail": [{"msg": ...}, ...]}`).
 */
async function parseErrorMessage(response: Response): Promise<{ message: string; code?: string }> {
  try {
    const body = await response.json();
    if (body?.error?.message) {
      return { message: body.error.message, code: body.error.code };
    }
    if (Array.isArray(body?.detail) && body.detail.length > 0) {
      return { message: body.detail.map((d: { msg: string }) => d.msg).join(", ") };
    }
    if (typeof body?.detail === "string") {
      return { message: body.detail };
    }
  } catch {
    // Response body wasn't JSON -- fall through to the generic message below.
  }
  return { message: `Request failed with status ${response.status}.` };
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(
      "Could not reach the VidAuditFlow API. Is the backend running?",
      0,
      "network_error",
    );
  }

  if (!response.ok) {
    const { message, code } = await parseErrorMessage(response);
    throw new ApiError(message, response.status, code);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function fetchAuditJobs(): Promise<AuditJob[]> {
  return apiFetch<AuditJob[]>("/api/v1/audits?limit=50");
}

export async function fetchAuditJob(id: string): Promise<AuditJob> {
  return apiFetch<AuditJob>(`/api/v1/audits/${id}`);
}

export async function createAudit(videoUrl: string): Promise<AuditJob> {
  return apiFetch<AuditJob>("/api/v1/audits", {
    method: "POST",
    body: JSON.stringify({ video_url: videoUrl }),
  });
}

export async function fetchReport(id: string): Promise<Report> {
  return apiFetch<Report>(`/api/v1/reports/${id}`);
}

/** AI Copilot: ask a question about a specific report (Phase 8). Stateless -- always send the full conversation so far. */
export async function sendReportChatMessage(
  reportId: string,
  message: string,
  conversation: ChatTurn[],
): Promise<ChatMessageResponse> {
  return apiFetch<ChatMessageResponse>(`/api/v1/reports/${reportId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, conversation }),
  });
}

/**
 * There is no `GET /api/v1/reports` list endpoint (see API_PLAN.md -- only
 * single-report fetch by id exists), so the "reports list" is composed
 * client-side: list audit jobs, keep the ones with a `report_id`, then
 * fetch each report. `Promise.allSettled` so one missing/failed report
 * doesn't blank the whole list.
 */
export async function fetchReports(): Promise<Report[]> {
  const jobs = await fetchAuditJobs();
  const jobsWithReports = jobs.filter((job) => job.report_id);

  const results = await Promise.allSettled(
    jobsWithReports.map((job) => fetchReport(job.report_id as string)),
  );

  return results
    .filter((result): result is PromiseFulfilledResult<Report> => result.status === "fulfilled")
    .map((result) => result.value)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}
