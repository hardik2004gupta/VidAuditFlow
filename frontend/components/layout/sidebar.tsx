import { Logo } from "@/components/layout/logo";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { Separator } from "@/components/ui/separator";

/**
 * Fixed desktop sidebar, ≥1024px only (UI_VISION.md Navigation: "Sidebar
 * (desktop, ≥1024px): fixed left, ~240px wide"). Below that breakpoint,
 * `SidebarMobile`'s drawer takes over.
 */
export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
      <div className="flex h-16 shrink-0 items-center px-4">
        <Logo />
      </div>
      <Separator />
      <div className="flex-1 overflow-y-auto py-4">
        <SidebarNav />
      </div>
      <div className="shrink-0 border-t border-sidebar-border p-4">
        <p className="text-xs text-muted-foreground">VidAuditFlow &middot; v0.1.0</p>
      </div>
    </aside>
  );
}
