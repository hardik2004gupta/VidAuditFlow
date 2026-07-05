import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SeverityBadge } from "@/features/audits/components/severity-badge";

describe("SeverityBadge", () => {
  it("renders the human-readable label for CRITICAL", () => {
    render(<SeverityBadge severity="CRITICAL" />);
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("renders the human-readable label for WARNING", () => {
    render(<SeverityBadge severity="WARNING" />);
    expect(screen.getByText("Warning")).toBeInTheDocument();
  });
});
