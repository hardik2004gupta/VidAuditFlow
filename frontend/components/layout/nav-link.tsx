"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface NavLinkProps {
  href: string;
  children: ReactNode;
  icon?: ReactNode;
  onNavigate?: () => void;
}

/**
 * Shared active-state nav link, used by both the desktop sidebar and the
 * mobile drawer so active-state logic only lives in one place.
 *
 * Active state: left-border accent + subtle background tint (UI_VISION.md
 * Navigation section, "Linear's exact active-nav-item pattern").
 */
export function NavLink({ href, children, icon, onNavigate }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      onClick={onNavigate}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "group flex h-10 items-center gap-2.5 rounded-lg border-l-2 px-3 text-sm font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar",
        isActive
          ? "border-l-primary bg-primary/10 text-foreground"
          : "border-l-transparent text-muted-foreground hover:bg-sidebar-accent hover:text-foreground",
      )}
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
