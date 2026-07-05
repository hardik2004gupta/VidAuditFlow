import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithQueryClient } from "@/test/test-utils";
import DashboardPage from "@/app/(dashboard)/dashboard/page";
import type { AuditJob, Report } from "@/types/api";

// `vi.mock` factories are hoisted above every other statement in the file,
// so the fixture data they close over must be declared via `vi.hoisted`
// rather than a plain `const` above them.
const { mockJob, mockReport } = vi.hoisted(() => {
  const mockJob: AuditJob = {
    id: "job-1",
    status: "completed",
    current_stage: "Completed",
    video_url: "https://youtu.be/abc123",
    video_id: "vid_abc123",
    error_message: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    report_id: "report-1",
  };

  const mockReport: Report = {
    id: "report-1",
    audit_job_id: "job-1",
    final_status: "PASS",
    confidence_score: 96,
    risk_level: "LOW",
    created_at: new Date().toISOString(),
    final_report: "All clear.",
    compliance_results: [],
    video_metadata: { duration: 120, platform: "youtube" },
    processing_metadata: [],
    warnings: [],
    sources: [],
  };

  return { mockJob, mockReport };
});

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    fetchAuditJobs: vi.fn().mockResolvedValue([mockJob]),
    fetchReports: vi.fn().mockResolvedValue([mockReport]),
  };
});

describe("DashboardPage", () => {
  it("renders the page header and metric/summary cards once data loads", async () => {
    renderWithQueryClient(<DashboardPage />);

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Recent Audits")).toBeInTheDocument();
    expect(screen.getByText("Recent Reports")).toBeInTheDocument();
    expect(screen.getByText("System Status")).toBeInTheDocument();
    expect(screen.getByText("Quick Actions")).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("vid_abc123")).toBeInTheDocument());
    expect(screen.getByText("Total Audits")).toBeInTheDocument();
  });
});
