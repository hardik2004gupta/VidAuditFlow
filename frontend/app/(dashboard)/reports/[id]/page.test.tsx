import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithQueryClient } from "@/test/test-utils";
import ReportPage from "@/app/(dashboard)/reports/[id]/page";
import type { Report } from "@/types/api";

const { mockReport } = vi.hoisted(() => {
  const mockReport: Report = {
    id: "ed334727-eb61-4d59-82e0-9e2f25e5880f",
    audit_job_id: "job-1",
    final_status: "FAIL",
    confidence_score: 34,
    risk_level: "HIGH",
    created_at: new Date().toISOString(),
    final_report:
      "## Executive Summary\nThis video scored 34/100 with 1 critical violation.\n\n## Suggested Fixes\n- Remove the guarantee language.",
    compliance_results: [
      {
        category: "Misleading Claims",
        severity: "CRITICAL",
        description: "Unsubstantiated guarantee.",
        timestamp: "00:32",
        confidence: 0.94,
        evidence: "I guarantee results.",
        policy_reference: "FTC Guide 3.2",
        recommendation: "Remove the guarantee language.",
      },
    ],
    video_metadata: { duration: 245, platform: "youtube" },
    processing_metadata: [
      {
        node: "summary_agent",
        status: "success",
        started_at: new Date().toISOString(),
        ended_at: new Date().toISOString(),
        duration_seconds: 1.2,
        error: null,
        tokens_used: null,
      },
    ],
    warnings: [],
    sources: [{ content: "Guarantee claims require substantiation.", source: "ftc-guide.pdf" }],
  };
  return { mockReport };
});

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, fetchReport: vi.fn().mockResolvedValue(mockReport) };
});

describe("ReportPage", () => {
  it("renders the report's executive summary, violations, and metadata", async () => {
    const element = await ReportPage({ params: Promise.resolve({ id: mockReport.id }) });
    renderWithQueryClient(element);

    expect(screen.getByRole("heading", { name: /report ed334727/i })).toBeInTheDocument();
    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    // Appears in both the Executive Summary's Top Findings preview and the
    // Violation Cards/Evidence Timeline sections -- multiple matches is correct.
    expect(screen.getAllByText("Misleading Claims").length).toBeGreaterThan(0);
    expect(screen.getByText("Evidence Timeline")).toBeInTheDocument();
    expect(screen.getByText("Report Details")).toBeInTheDocument();
    // The score gauge's number is animated (Framer Motion count-up from 0),
    // so assert the static parts of that card instead of the moving number.
    expect(screen.getByText("out of 100")).toBeInTheDocument();
    expect(screen.getByText("High Risk")).toBeInTheDocument();
  });

  it("calls notFound() for a report that doesn't exist", async () => {
    const { fetchReport, ApiError } = await import("@/lib/api");
    vi.mocked(fetchReport).mockRejectedValueOnce(new ApiError("Report not found", 404));

    await expect(ReportPage({ params: Promise.resolve({ id: "missing" }) })).rejects.toThrow();
  });
});
