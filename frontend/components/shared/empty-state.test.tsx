import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { ShieldCheck } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

describe("EmptyState", () => {
  it("renders a title and optional description", () => {
    render(<EmptyState icon={ShieldCheck} title="No violations detected" description="All clear." />);

    expect(screen.getByText("No violations detected")).toBeInTheDocument();
    expect(screen.getByText("All clear.")).toBeInTheDocument();
  });

  it("renders an optional action and lets it be interacted with", async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <EmptyState
        icon={ShieldCheck}
        title="No audits yet"
        action={<button onClick={onClick}>Start an audit</button>}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Start an audit" }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
