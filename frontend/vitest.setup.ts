import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => {
  cleanup();
});

// jsdom doesn't implement matchMedia -- next-themes and useMediaQuery both
// call it on mount, so every test needs a stub even if it never touches
// theming/breakpoints directly.
window.matchMedia =
  window.matchMedia ||
  ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));

// jsdom doesn't implement scrollIntoView (used by CopilotPanel's
// auto-scroll-to-latest-message effect).
Element.prototype.scrollIntoView = Element.prototype.scrollIntoView || vi.fn();
