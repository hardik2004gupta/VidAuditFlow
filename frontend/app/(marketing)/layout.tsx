import type { ReactNode } from "react";
import { SiteHeader } from "@/features/landing/components/site-header";
import { SiteFooter } from "@/features/landing/components/site-footer";

export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">{children}</main>
      <SiteFooter />
    </div>
  );
}
