import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { renderWithQueryClient } from "@/test/test-utils";
import { CopilotPanel } from "@/features/reports/components/copilot/copilot-panel";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, sendReportChatMessage: vi.fn() };
});

describe("CopilotPanel", () => {
  it("shows the empty state with all four suggested prompts", () => {
    renderWithQueryClient(<CopilotPanel reportId="report-1" onClose={vi.fn()} />);

    expect(screen.getByText("Ask about this report")).toBeInTheDocument();
    expect(screen.getByText("Summarize report")).toBeInTheDocument();
    expect(screen.getByText("Highest risk issues")).toBeInTheDocument();
    expect(screen.getByText("Explain recommendations")).toBeInTheDocument();
    expect(screen.getByText("Next steps")).toBeInTheDocument();
  });

  it("calls onClose when the close button is clicked", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithQueryClient(<CopilotPanel reportId="report-1" onClose={onClose} />);

    await user.click(screen.getByRole("button", { name: /close ai copilot/i }));

    expect(onClose).toHaveBeenCalledOnce();
  });

  it("sends a message when a suggested prompt is clicked and renders the reply", async () => {
    const { sendReportChatMessage } = await import("@/lib/api");
    vi.mocked(sendReportChatMessage).mockResolvedValue({ reply: "This report has one critical violation." });

    const user = userEvent.setup();
    renderWithQueryClient(<CopilotPanel reportId="report-1" onClose={vi.fn()} />);

    await user.click(screen.getByText("Summarize report"));

    expect(screen.getByText("Summarize this report.")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("This report has one critical violation.")).toBeInTheDocument(),
    );
    expect(sendReportChatMessage).toHaveBeenCalledWith("report-1", "Summarize this report.", []);
  });

  it("shows an error with a retry button when the request fails", async () => {
    const { sendReportChatMessage, ApiError } = await import("@/lib/api");
    vi.mocked(sendReportChatMessage).mockRejectedValue(new ApiError("Upstream error", 502));

    const user = userEvent.setup();
    renderWithQueryClient(<CopilotPanel reportId="report-1" onClose={vi.fn()} />);

    await user.click(screen.getByText("Next steps"));

    expect(await screen.findByText("Upstream error")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });
});
