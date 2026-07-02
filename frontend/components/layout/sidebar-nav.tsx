import { FileText, LayoutDashboard, PlusCircle, Settings } from "lucide-react";
import { NavLink } from "@/components/layout/nav-link";
import { NAV_ITEMS } from "@/lib/constants";

const NAV_ICONS: Record<string, typeof LayoutDashboard> = {
  "/dashboard": LayoutDashboard,
  "/audits/new": PlusCircle,
  "/reports": FileText,
  "/settings": Settings,
};

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1 px-3" aria-label="Primary">
      {NAV_ITEMS.map((item) => {
        const Icon = NAV_ICONS[item.href];
        return (
          <NavLink key={item.href} href={item.href} icon={<Icon className="size-4" />} onNavigate={onNavigate}>
            {item.label}
          </NavLink>
        );
      })}
    </nav>
  );
}
