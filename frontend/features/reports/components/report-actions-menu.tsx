"use client";

import { toast } from "sonner";
import { ClipboardCheck, ClipboardList, Copy, Download, FileJson, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  buildEvidenceText,
  buildRecommendationsText,
  buildSummaryText,
  downloadReportJson,
} from "@/lib/report-export";
import type { Report } from "@/types/api";

async function copyText(text: string, successMessage: string) {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(successMessage);
  } catch {
    toast.error("Couldn't copy to clipboard -- your browser may have blocked it.");
  }
}

/** Report page header action: copy/export options for sharing a report outside the app. */
export function ReportActionsMenu({ report }: { report: Report }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="outline" size="sm" />}>
        <Share2 className="size-4" data-icon="inline-start" />
        Export
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem onClick={() => copyText(buildSummaryText(report), "Summary copied to clipboard")}>
          <Copy className="size-4" data-icon="inline-start" />
          Copy Summary
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => copyText(buildRecommendationsText(report), "Recommendations copied to clipboard")}
        >
          <ClipboardList className="size-4" data-icon="inline-start" />
          Copy Recommendations
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => copyText(buildEvidenceText(report), "Evidence copied to clipboard")}>
          <ClipboardCheck className="size-4" data-icon="inline-start" />
          Copy Evidence
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => copyText(JSON.stringify(report, null, 2), "Report JSON copied to clipboard")}
        >
          <FileJson className="size-4" data-icon="inline-start" />
          Copy Report JSON
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => {
            downloadReportJson(report);
            toast.success("Report JSON downloaded");
          }}
        >
          <Download className="size-4" data-icon="inline-start" />
          Download JSON
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
