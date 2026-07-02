/**
 * Extracts the body text under a `## {heading}` line in a Report's
 * `final_report` markdown, up to the next `## ` heading or end of string.
 * Deliberately not a full markdown renderer -- the structured fields
 * (confidence_score, risk_level, compliance_results) already back every
 * other section; this only recovers the free-text prose/lists.
 */
export function extractMarkdownSection(markdown: string, heading: string): string {
  const pattern = new RegExp(`##\\s+${heading}\\s*\\n([\\s\\S]*?)(?=\\n##\\s+|$)`, "i");
  const match = markdown.match(pattern);
  return match ? match[1].trim() : "";
}

/** Splits a markdown bullet-list block ("- item\n- item") into plain strings. */
export function parseMarkdownList(block: string): string[] {
  return block
    .split("\n")
    .map((line) => line.replace(/^-\s*/, "").replace(/\*\*/g, "").trim())
    .filter(Boolean);
}
