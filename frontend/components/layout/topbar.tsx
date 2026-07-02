import { SidebarMobile } from "@/components/layout/sidebar-mobile";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { UserMenu } from "@/components/layout/user-menu";

/**
 * Slim, persistent topbar. Uses backdrop-blur + a semi-transparent
 * background when content scrolls beneath it -- one of UI_VISION.md's two
 * sanctioned glassmorphism spots (the other being dialog overlays).
 */
export function Topbar() {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-2 border-b border-border bg-background/80 px-4 backdrop-blur-md supports-[backdrop-filter]:bg-background/60 lg:px-8">
      <SidebarMobile />
      <div className="flex-1" />
      <ThemeToggle />
      <UserMenu />
    </header>
  );
}
