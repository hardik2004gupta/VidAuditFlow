import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { renderWithQueryClient } from "@/test/test-utils";
import { NewAuditForm } from "@/features/audits/components/new-audit-form";

vi.mock("@/lib/api", () => ({
  createAudit: vi.fn(),
  fetchAuditJob: vi.fn(),
}));

describe("NewAuditForm validation", () => {
  it("rejects an empty submission with a required-field message", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<NewAuditForm />);

    await user.click(screen.getByRole("button", { name: /analyze video/i }));

    expect(await screen.findByText("A video URL is required.")).toBeInTheDocument();
  });

  it("rejects a non-YouTube URL with a validation message", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<NewAuditForm />);

    await user.type(screen.getByLabelText(/youtube video url/i), "https://example.com/not-youtube");
    await user.click(screen.getByRole("button", { name: /analyze video/i }));

    expect(await screen.findByText("Enter a valid YouTube video URL.")).toBeInTheDocument();
  });

  it("accepts a valid YouTube URL and submits without a validation error", async () => {
    const { createAudit } = await import("@/lib/api");
    vi.mocked(createAudit).mockResolvedValue({
      id: "job-1",
      status: "queued",
      current_stage: null,
      video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      video_id: "vid_12345678",
      error_message: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      completed_at: null,
      report_id: null,
    });

    const user = userEvent.setup();
    renderWithQueryClient(<NewAuditForm />);

    await user.type(
      screen.getByLabelText(/youtube video url/i),
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    );
    await user.click(screen.getByRole("button", { name: /analyze video/i }));

    // TanStack Query v5 calls mutationFn as (variables, context) -- assert
    // just the first argument, the video URL this component actually sends.
    await waitFor(() => expect(createAudit).toHaveBeenCalled());
    expect(vi.mocked(createAudit).mock.calls[0][0]).toBe("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
    expect(screen.queryByText("Enter a valid YouTube video URL.")).not.toBeInTheDocument();
  });
});
