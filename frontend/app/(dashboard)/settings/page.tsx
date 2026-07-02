import { Wrench } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { AppearanceSettingsCard } from "@/features/settings/components/appearance-settings-card";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your VidAuditFlow preferences."
        breadcrumb={[{ label: "Dashboard", href: "/dashboard" }, { label: "Settings" }]}
      />
      <div className="max-w-2xl space-y-6">
        <AppearanceSettingsCard />
        <EmptyState
          icon={Wrench}
          title="More settings coming soon"
          description="Account, workspace, and notification preferences will appear here once authentication is introduced."
        />
      </div>
    </div>
  );
}
