import { Logo } from "@/components/layout/logo";

export function SiteFooter() {
  return (
    <footer className="border-t border-border">
      <div className="content-container flex flex-col items-center justify-between gap-4 py-8 sm:flex-row">
        <Logo />
        <p className="text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} VidAuditFlow. Built for compliance teams.
        </p>
      </div>
    </footer>
  );
}
