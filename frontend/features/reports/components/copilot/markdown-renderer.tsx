import type { ReactNode } from "react";
import { Fragment } from "react";

/**
 * A deliberately small, hand-rolled Markdown renderer -- consistent with
 * this codebase's existing `lib/markdown.ts` (which also hand-parses
 * `final_report` instead of pulling in a markdown library). Supports
 * exactly what an LLM chat reply realistically produces: paragraphs, bold,
 * inline code, fenced code blocks, and bullet/numbered lists. Not a general
 * CommonMark implementation.
 */
export function MarkdownRenderer({ content }: { content: string }) {
  const blocks = parseBlocks(content);
  return (
    <div className="space-y-2.5 text-sm leading-relaxed">
      {blocks.map((block, index) => (
        <Fragment key={index}>{renderBlock(block)}</Fragment>
      ))}
    </div>
  );
}

type Block =
  | { type: "paragraph"; text: string }
  | { type: "code"; code: string; language?: string }
  | { type: "list"; ordered: boolean; items: string[] };

function parseBlocks(content: string): Block[] {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim() === "") {
      i += 1;
      continue;
    }

    // Fenced code block: ```lang \n ... \n ```
    const fenceMatch = line.match(/^```(\w*)/);
    if (fenceMatch) {
      const language = fenceMatch[1] || undefined;
      const codeLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i += 1;
      }
      i += 1; // skip closing fence
      blocks.push({ type: "code", code: codeLines.join("\n"), language });
      continue;
    }

    // Bullet or numbered list -- consume consecutive list lines of the same kind.
    const bulletMatch = line.match(/^\s*[-*]\s+(.*)/);
    const numberedMatch = line.match(/^\s*\d+[.)]\s+(.*)/);
    if (bulletMatch || numberedMatch) {
      const ordered = !!numberedMatch;
      const items: string[] = [];
      while (i < lines.length) {
        const itemMatch = ordered ? lines[i].match(/^\s*\d+[.)]\s+(.*)/) : lines[i].match(/^\s*[-*]\s+(.*)/);
        if (!itemMatch) break;
        items.push(itemMatch[1]);
        i += 1;
      }
      blocks.push({ type: "list", ordered, items });
      continue;
    }

    // Paragraph: consume until a blank line or the start of a list/fence.
    const paragraphLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].match(/^```/) &&
      !lines[i].match(/^\s*[-*]\s+/) &&
      !lines[i].match(/^\s*\d+[.)]\s+/)
    ) {
      paragraphLines.push(lines[i]);
      i += 1;
    }
    blocks.push({ type: "paragraph", text: paragraphLines.join(" ") });
  }

  return blocks;
}

function renderBlock(block: Block): ReactNode {
  if (block.type === "code") {
    return (
      <pre className="font-technical overflow-x-auto rounded-lg border border-border bg-muted/40 p-3 text-xs">
        <code>{block.code}</code>
      </pre>
    );
  }
  if (block.type === "list") {
    const ListTag = block.ordered ? "ol" : "ul";
    return (
      <ListTag className={block.ordered ? "list-inside list-decimal space-y-1" : "list-inside list-disc space-y-1"}>
        {block.items.map((item, index) => (
          <li key={index}>{renderInline(item)}</li>
        ))}
      </ListTag>
    );
  }
  return <p>{renderInline(block.text)}</p>;
}

/** Applies inline `**bold**` and `` `code` `` formatting within a line of text. */
function renderInline(text: string): ReactNode[] {
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  const parts = text.split(pattern).filter((part) => part !== "");

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={index} className="font-technical rounded bg-muted px-1 py-0.5 text-[0.85em]">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <Fragment key={index}>{part}</Fragment>;
  });
}
