import { FileText, ScanText, Search, ShieldAlert, FileCheck2, GitBranch } from "lucide-react";
import { SectionHeader } from "@/components/shared/section-header";

const FEATURES = [
  {
    icon: FileText,
    title: "Transcript extraction",
    description:
      "Downloads the video and transcribes every spoken word, timestamped for precise evidence citations.",
  },
  {
    icon: ScanText,
    title: "On-screen text (OCR)",
    description:
      "Reads captions, disclosures, and on-screen graphics that spoken transcripts alone would miss.",
  },
  {
    icon: Search,
    title: "Policy retrieval",
    description:
      "Retrieves the exact advertising and platform policy passages relevant to this specific video's content.",
  },
  {
    icon: ShieldAlert,
    title: "Compliance analysis",
    description:
      "Cross-references transcript, on-screen text, and policy to flag violations by category and severity.",
  },
  {
    icon: FileCheck2,
    title: "Evidence-backed reporting",
    description:
      "Every finding ships with a direct quote, confidence score, policy reference, and recommendation.",
  },
  {
    icon: GitBranch,
    title: "Supervisor-orchestrated pipeline",
    description:
      "A LangGraph supervisor coordinates five specialist agents end-to-end, with full stage-by-stage observability.",
  },
] as const;

export function FeaturesSection() {
  return (
    <section id="features" className="content-container py-16 sm:py-24">
      <SectionHeader
        title="Everything a compliance review needs"
        description="One pipeline run replaces hours of manual transcript review, screenshot combing, and policy cross-checking."
      />
      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className="rounded-lg border border-border bg-card p-5 transition-colors hover:border-primary/40"
          >
            <div className="mb-4 flex size-10 items-center justify-center rounded-lg bg-primary/10">
              <feature.icon className="size-5 text-primary" aria-hidden="true" />
            </div>
            <h3 className="text-sm font-semibold text-foreground">{feature.title}</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">{feature.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
