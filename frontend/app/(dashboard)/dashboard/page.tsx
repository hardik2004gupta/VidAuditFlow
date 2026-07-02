import Link from "next/link";
import { PlusCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { DashboardMetrics } from "@/features/dashboard/components/dashboard-metrics";
import { RecentAuditsCard } from "@/features/dashboard/components/recent-audits-card";
import { RecentReportsCard } from "@/features/dashboard/components/recent-reports-card";
import { SystemStatusCard } from "@/features/dashboard/components/system-status-card";
import { QuickActionsCard } from "@/features/dashboard/components/quick-actions-card";

export default function DashboardPage() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="An overview of your recent compliance audits and reports."
        action={
          <Button render={<Link href="/audits/new" />}>
            <PlusCircle className="size-4" data-icon="inline-start" />
            New Audit
          </Button>
        }
      />

      <div className="space-y-6">
        <DashboardMetrics />

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <RecentAuditsCard />
            <RecentReportsCard />
          </div>
          <div className="space-y-6">
            <SystemStatusCard />
            <QuickActionsCard />
          </div>
        </div>
      </div>
    </div>
  );
}
