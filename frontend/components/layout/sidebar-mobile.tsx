"use client";

import { Menu } from "lucide-react";
import { useState } from "react";
import { Logo } from "@/components/layout/logo";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

/**
 * Mobile/tablet nav drawer (<1024px). UI_VISION.md Navigation: "sidebar
 * collapses to a slide-over drawer triggered by a hamburger icon"; a
 * bottom nav is deliberately avoided ("too app-like for a dashboard
 * product").
 */
export function SidebarMobile() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        aria-label="Open navigation menu"
        onClick={() => setOpen(true)}
      >
        <Menu className="size-5" />
      </Button>
      <SheetContent side="left" className="w-64 gap-0 bg-sidebar p-0">
        <SheetHeader className="h-16 justify-center border-b border-sidebar-border px-4 py-0">
          <SheetTitle className="sr-only">Navigation menu</SheetTitle>
          <Logo />
        </SheetHeader>
        <div className="flex-1 overflow-y-auto py-4">
          <SidebarNav onNavigate={() => setOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
