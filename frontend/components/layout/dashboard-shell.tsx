import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

/** The authenticated-feel app shell: sidebar + topbar + a consistent-width content container. */
export function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-svh bg-background">
      <Sidebar />
      <div className="flex min-h-svh flex-col lg:pl-60">
        <Topbar />
        <main className="content-container flex-1 py-8 lg:py-10">{children}</main>
      </div>
    </div>
  );
}
