import { Settings } from "lucide-react";
import Link from "next/link";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/**
 * No authentication exists in this phase (see PHASE_5_SUMMARY.md) -- this
 * shows a static demo-workspace identity and a link to Settings only.
 * Deliberately no "Sign out" item: there is no real session to end, and
 * adding one would misrepresent auth as implemented when it isn't.
 */
export function UserMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="ghost" className="h-9 gap-2 rounded-full px-1.5" aria-label="Open user menu" />
        }
      >
        <Avatar size="sm">
          <AvatarFallback className="bg-primary/15 text-primary">VA</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel className="font-normal">
          <p className="text-sm font-medium">Demo Workspace</p>
          <p className="text-xs text-muted-foreground">No account connected</p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem render={<Link href="/settings" />}>
          <Settings className="size-4" />
          Settings
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
