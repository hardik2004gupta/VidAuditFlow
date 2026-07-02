"use client";

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";

export function WarningsBanner({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex gap-3 rounded-lg border border-warning/20 bg-warning/5 p-4"
    >
      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-warning/10">
        <AlertTriangle className="size-4 text-warning" aria-hidden="true" />
      </span>
      <div className="space-y-1.5">
        <p className="text-sm font-medium text-foreground">This report was generated with degraded input</p>
        <ul className="space-y-1 text-sm text-muted-foreground">
          {warnings.map((warning) => (
            <li key={warning} className="flex gap-1.5">
              <span aria-hidden="true">&middot;</span>
              <span>{warning}</span>
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}
