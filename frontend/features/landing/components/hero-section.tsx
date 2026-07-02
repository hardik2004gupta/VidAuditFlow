"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function HeroSection() {
  return (
    <section className="content-container flex flex-col items-center gap-8 py-20 text-center sm:py-28">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground"
      >
        <Sparkles className="size-3.5 text-primary" aria-hidden="true" />
        Multi-agent compliance analysis, in minutes
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.05 }}
        className="max-w-3xl text-4xl font-bold tracking-tight text-foreground sm:text-5xl sm:leading-[1.1]"
      >
        Audit any video for compliance risk before it goes live
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.1 }}
        className="max-w-xl text-balance text-base text-muted-foreground sm:text-lg"
      >
        Paste a YouTube URL and VidAuditFlow&rsquo;s supervisor-orchestrated AI pipeline
        transcribes, reads on-screen text, retrieves policy, and reports every violation
        with evidence and citations.
      </motion.p>

      <motion.form
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.15 }}
        className="flex w-full max-w-lg flex-col gap-2 sm:flex-row"
        onSubmit={(event) => event.preventDefault()}
      >
        <Input
          type="url"
          placeholder="https://www.youtube.com/watch?v=..."
          aria-label="YouTube video URL"
          className="h-11 flex-1"
        />
        <Button size="lg" className="h-11" render={<Link href="/audits/new" />}>
          Analyze video
          <ArrowRight className="size-4" data-icon="inline-end" />
        </Button>
      </motion.form>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.45, delay: 0.2 }}
        className="text-xs text-muted-foreground"
      >
        No sign-up required for this preview &middot; 7-stage LangGraph pipeline
      </motion.p>
    </section>
  );
}
