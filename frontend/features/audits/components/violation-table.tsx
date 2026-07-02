"use client";

import { useState } from "react";
import { Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/shared/empty-state";
import { SeverityBadge } from "@/features/audits/components/severity-badge";
import { EvidenceCard } from "@/features/audits/components/evidence-card";
import { ShieldCheck } from "lucide-react";
import type { ComplianceIssue } from "@/types/api";

interface ViolationTableProps {
  violations: ComplianceIssue[];
}

/** Stripe-Dashboard-style table of compliance violations, each row expandable via dialog. */
export function ViolationTable({ violations }: ViolationTableProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const activeIssue = activeIndex != null ? violations[activeIndex] : null;

  if (violations.length === 0) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="No violations detected"
        description="This video passed compliance analysis with no flagged issues."
      />
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Severity</TableHead>
              <TableHead>Category</TableHead>
              <TableHead className="hidden md:table-cell">Description</TableHead>
              <TableHead className="text-right">Confidence</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {violations.map((issue, index) => (
              <TableRow
                key={`${issue.category}-${index}`}
                className="cursor-pointer"
                onClick={() => setActiveIndex(index)}
              >
                <TableCell>
                  <SeverityBadge severity={issue.severity} />
                </TableCell>
                <TableCell className="font-medium text-foreground">{issue.category}</TableCell>
                <TableCell className="hidden max-w-md truncate text-muted-foreground md:table-cell">
                  {issue.description}
                </TableCell>
                <TableCell className="text-right font-technical tabular-nums text-muted-foreground">
                  {Math.round(issue.confidence * 100)}%
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label={`View evidence for ${issue.category}`}
                    onClick={(event) => {
                      event.stopPropagation();
                      setActiveIndex(index);
                    }}
                  >
                    <Eye className="size-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={activeIndex != null} onOpenChange={(open) => !open && setActiveIndex(null)}>
        <DialogContent className="max-w-lg sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{activeIssue?.category}</DialogTitle>
            <DialogDescription>Full evidence and recommendation for this violation.</DialogDescription>
          </DialogHeader>
          {activeIssue && <EvidenceCard issue={activeIssue} />}
        </DialogContent>
      </Dialog>
    </>
  );
}
