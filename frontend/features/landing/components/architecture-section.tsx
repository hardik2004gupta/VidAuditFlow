import { SectionHeader } from "@/components/shared/section-header";
import { PIPELINE_STAGES } from "@/types/api";

export function ArchitectureSection() {
  return (
    <section id="architecture" className="content-container py-16 sm:py-24">
      <SectionHeader
        title="A supervisor-orchestrated LangGraph pipeline"
        description="One supervisor node dispatches work to five specialist agents and validates their output before the report is generated."
      />
      <div className="overflow-x-auto rounded-lg border border-border bg-card p-6">
        <ol className="flex min-w-max items-center gap-2">
          {PIPELINE_STAGES.map((stage, index) => (
            <li key={stage.key} className="flex items-center gap-2">
              <div className="flex w-40 flex-col gap-1 rounded-lg border border-border bg-background px-3 py-2.5">
                <span className="font-technical text-[11px] text-muted-foreground">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="text-xs font-medium text-foreground">{stage.label}</span>
              </div>
              {index < PIPELINE_STAGES.length - 1 && (
                <span className="h-px w-6 shrink-0 bg-border" aria-hidden="true" />
              )}
            </li>
          ))}
        </ol>
      </div>
      <p className="mt-4 text-sm text-muted-foreground">
        Every stage is traced -- duration, token usage, and failures are recorded and
        surfaced in the report&rsquo;s processing timeline, not hidden inside a black box.
      </p>
    </section>
  );
}
