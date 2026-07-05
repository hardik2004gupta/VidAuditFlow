import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Activity } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";

describe("MetricCard", () => {
  it("renders the label, value, and optional hint", () => {
    render(<MetricCard label="Total Audits" value="6" hint="+2 this week" icon={Activity} />);

    expect(screen.getByText("Total Audits")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("+2 this week")).toBeInTheDocument();
  });

  it("omits the hint when none is given", () => {
    render(<MetricCard label="Active Jobs" value="2" icon={Activity} />);

    expect(screen.getByText("Active Jobs")).toBeInTheDocument();
    expect(screen.queryByText("+2 this week")).not.toBeInTheDocument();
  });
});
