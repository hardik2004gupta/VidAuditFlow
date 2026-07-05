import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { StageTracker } from "@/features/audits/components/stage-tracker";
import type { StageProgress } from "@/hooks/use-audit-job-polling";

function stage(overrides: Partial<StageProgress>): StageProgress {
  return {
    key: "transcript_agent",
    label: "Downloading Video & Extracting Transcript",
    state: "pending",
    elapsedSeconds: null,
    ...overrides,
  };
}

describe("StageTracker", () => {
  it("renders every stage's label", () => {
    render(
      <StageTracker
        progressRatio={0.5}
        stages={[
          stage({ key: "supervisor_start", label: "Starting Audit", state: "done", elapsedSeconds: 1.2 }),
          stage({ key: "transcript_agent", label: "Downloading Video", state: "active" }),
          stage({ key: "ocr_agent", label: "Extracting OCR", state: "pending" }),
        ]}
      />,
    );

    expect(screen.getByText("Starting Audit")).toBeInTheDocument();
    expect(screen.getByText("Downloading Video")).toBeInTheDocument();
    expect(screen.getByText("Extracting OCR")).toBeInTheDocument();
  });

  it("shows elapsed time only for stages that have one", () => {
    render(
      <StageTracker
        progressRatio={0.3}
        stages={[
          stage({ key: "supervisor_start", label: "Starting Audit", state: "done", elapsedSeconds: 1.2 }),
          stage({ key: "transcript_agent", label: "Downloading Video", state: "active", elapsedSeconds: null }),
        ]}
      />,
    );

    expect(screen.getByText("1.2s")).toBeInTheDocument();
  });

  it("renders a progress bar reflecting progressRatio", () => {
    render(<StageTracker progressRatio={0.75} stages={[stage({ state: "active" })]} />);

    const progress = screen.getByRole("progressbar");
    expect(progress).toHaveAttribute("aria-valuenow", "75");
  });

  it("renders the error state distinctly for a failed stage", () => {
    render(
      <StageTracker
        progressRatio={0.4}
        stages={[stage({ key: "transcript_agent", label: "Downloading Video", state: "error" })]}
      />,
    );

    expect(screen.getByText("Downloading Video")).toBeInTheDocument();
  });
});
