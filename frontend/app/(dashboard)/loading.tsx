import { Skeleton } from "@/components/ui/skeleton";

/**
 * Route-level loading boundary. UI_VISION.md: "No blank spinners for
 * anything longer than ~1 second" -- every loading surface is a skeleton
 * shaped like the eventual content, not a generic spinner.
 */
export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-64" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-28 rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-72 rounded-lg" />
    </div>
  );
}
