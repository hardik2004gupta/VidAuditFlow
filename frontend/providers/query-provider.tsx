"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, type ReactNode } from "react";

/**
 * TanStack Query provider. Even though this phase uses the mock data layer
 * (lib/mock/) instead of real HTTP calls, every data-fetching hook already
 * goes through `useQuery`/`useMutation` -- so when real backend integration
 * lands, only the query functions change, not the data layer's shape,
 * caching behavior, or loading/error states any component relies on.
 *
 * No optimistic updates, no persistence/caching beyond React Query's
 * in-memory default -- explicitly out of scope for this phase.
 */
export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      {children}
      {process.env.NODE_ENV === "development" && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
