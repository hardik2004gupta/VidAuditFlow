import Link from "next/link";
import { PlusCircle, FileText, Settings } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const ACTIONS = [
  { href: "/audits/new", label: "New Audit", icon: PlusCircle },
  { href: "/reports", label: "View Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function QuickActionsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {ACTIONS.map((action) => (
          <Button
            key={action.href}
            variant="outline"
            className="w-full justify-start"
            render={<Link href={action.href} />}
          >
            <action.icon className="size-4" data-icon="inline-start" />
            {action.label}
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
