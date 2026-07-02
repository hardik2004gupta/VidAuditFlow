import { PageHeader } from "@/components/layout/page-header";
import { ReportsTable } from "@/features/reports/components/reports-table";

export default function ReportsPage() {
  return (
    <div>
      <PageHeader
        title="Reports"
        description="All compliance reports generated from completed audits."
        breadcrumb={[{ label: "Dashboard", href: "/dashboard" }, { label: "Reports" }]}
      />
      <ReportsTable />
    </div>
  );
}
