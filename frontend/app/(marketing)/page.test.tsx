import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import LandingPage from "@/app/(marketing)/page";

describe("LandingPage", () => {
  it("renders the hero headline and primary call to action", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", { name: /audit any video for compliance risk before it goes live/i }),
    ).toBeInTheDocument();
    // The design system's Button renders as a polymorphic <a> with an
    // explicit role="button" override (see Phase 6's nativeButton fix) --
    // it's a link in the DOM, but accessibility-wise a button.
    expect(screen.getByRole("button", { name: /analyze video/i })).toBeInTheDocument();
  });

  it("renders every marketing section", () => {
    render(<LandingPage />);

    expect(screen.getByText(/everything a compliance review needs/i)).toBeInTheDocument();
    expect(screen.getByText(/a supervisor-orchestrated langgraph pipeline/i)).toBeInTheDocument();
    expect(screen.getByText(/built on a modern, boring-on-purpose stack/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /run your first audit/i })).toBeInTheDocument();
  });
});
