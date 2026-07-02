import type { AuditJobStatus, RiskLevel, Severity } from "@/types/api";

/**
 * Centralized status/severity -> label + style mapping.
 *
 * Per UI_VISION.md's color-palette rule ("severity colors are reserved
 * exclusively for compliance status"), every className here uses only the
 * four domain tokens (success/warning/critical/info) or neutral muted --
 * never the brand `primary` color, which stays reserved for CTAs/active
 * nav/links.
 */

export const AUDIT_STATUS_CONFIG: Record<
  AuditJobStatus,
  { label: string; badgeClassName: string }
> = {
  queued: {
    label: "Queued",
    badgeClassName: "bg-muted text-muted-foreground border-border",
  },
  running: {
    label: "Running",
    badgeClassName: "bg-info/10 text-info border-info/20",
  },
  completed: {
    label: "Completed",
    badgeClassName: "bg-success/10 text-success border-success/20",
  },
  completed_degraded: {
    label: "Completed (Degraded)",
    badgeClassName: "bg-warning/10 text-warning border-warning/20",
  },
  failed: {
    label: "Failed",
    badgeClassName: "bg-critical/10 text-critical border-critical/20",
  },
  cancelled: {
    label: "Cancelled",
    badgeClassName: "bg-muted text-muted-foreground border-border",
  },
};

export const SEVERITY_CONFIG: Record<Severity, { label: string; badgeClassName: string }> = {
  CRITICAL: {
    label: "Critical",
    badgeClassName: "bg-critical/10 text-critical border-critical/20",
  },
  WARNING: {
    label: "Warning",
    badgeClassName: "bg-warning/10 text-warning border-warning/20",
  },
};

export const RISK_LEVEL_CONFIG: Record<RiskLevel, { label: string; badgeClassName: string; barClassName: string }> = {
  LOW: {
    label: "Low Risk",
    badgeClassName: "bg-success/10 text-success border-success/20",
    barClassName: "bg-success",
  },
  MEDIUM: {
    label: "Medium Risk",
    badgeClassName: "bg-warning/10 text-warning border-warning/20",
    barClassName: "bg-warning",
  },
  HIGH: {
    label: "High Risk",
    badgeClassName: "bg-critical/10 text-critical border-critical/20",
    barClassName: "bg-critical",
  },
};

export const FINAL_STATUS_CONFIG: Record<"PASS" | "FAIL", { label: string; badgeClassName: string }> = {
  PASS: { label: "Pass", badgeClassName: "bg-success/10 text-success border-success/20" },
  FAIL: { label: "Fail", badgeClassName: "bg-critical/10 text-critical border-critical/20" },
};

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/audits/new", label: "New Audit" },
  { href: "/reports", label: "Reports" },
  { href: "/settings", label: "Settings" },
] as const;
