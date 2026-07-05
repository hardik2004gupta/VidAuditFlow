import { describe, expect, it } from "vitest";
import { formatDuration, formatStageDuration, parseTimestampToSeconds, shortId } from "@/lib/format";

describe("formatDuration", () => {
  it("formats seconds as mm:ss", () => {
    expect(formatDuration(65)).toBe("1:05");
    expect(formatDuration(0)).toBe("0:00");
  });

  it("returns an em dash for null/undefined", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(undefined)).toBe("—");
  });
});

describe("formatStageDuration", () => {
  it("formats sub-second durations in ms", () => {
    expect(formatStageDuration(0.82)).toBe("820ms");
  });

  it("formats seconds with one decimal", () => {
    expect(formatStageDuration(14.9)).toBe("14.9s");
  });

  it("formats minutes+seconds once over a minute", () => {
    expect(formatStageDuration(125)).toBe("2m 5s");
  });
});

describe("parseTimestampToSeconds", () => {
  it("parses mm:ss", () => {
    expect(parseTimestampToSeconds("01:14")).toBe(74);
  });

  it("returns null for missing/unparseable input", () => {
    expect(parseTimestampToSeconds(null)).toBeNull();
    expect(parseTimestampToSeconds("not-a-timestamp")).toBeNull();
  });
});

describe("shortId", () => {
  it("strips hyphens and truncates to 8 characters", () => {
    expect(shortId("ed334727-eb61-4d59-82e0-9e2f25e5880f")).toBe("ed334727");
  });
});
