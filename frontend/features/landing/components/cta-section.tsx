import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CtaSection() {
  return (
    <section className="content-container py-16 sm:py-24">
      <div className="flex flex-col items-center gap-5 rounded-lg border border-border bg-card px-6 py-14 text-center">
        <h2 className="max-w-lg text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Run your first audit in the time it takes to read this sentence out loud
        </h2>
        <p className="max-w-md text-sm text-muted-foreground">
          Paste a video URL, watch the pipeline work stage by stage, and get a
          citation-backed compliance report.
        </p>
        <Button size="lg" render={<Link href="/audits/new" />}>
          Start an audit
          <ArrowRight className="size-4" data-icon="inline-end" />
        </Button>
      </div>
    </section>
  );
}
