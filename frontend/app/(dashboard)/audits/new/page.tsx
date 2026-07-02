import { PageHeader } from "@/components/layout/page-header";
import { NewAuditForm } from "@/features/audits/components/new-audit-form";
import { RecentAuditsCard } from "@/features/dashboard/components/recent-audits-card";

export default function NewAuditPage() {
  return (
    <div>
      <PageHeader
        title="New Audit"
        description="Paste a YouTube video URL to run it through the compliance pipeline."
        breadcrumb={[{ label: "Dashboard", href: "/dashboard" }, { label: "New Audit" }]}
      />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <NewAuditForm />
        </div>
        <div>
          <RecentAuditsCard />
        </div>
      </div>
    </div>
  );
}
