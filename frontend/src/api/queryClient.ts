import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { ApiError } from "./client";

/**
 * No retries: 4xx answers are final, and retrying a 404 or 401 only delays the UI.
 * `onUnauthorized` runs when any request answers 401 (session expired).
 */
export function makeQueryClient(onUnauthorized: () => void = () => undefined): QueryClient {
  const onError = (error: Error) => {
    if (error instanceof ApiError && error.status === 401) onUnauthorized();
  };
  return new QueryClient({
    queryCache: new QueryCache({ onError }),
    mutationCache: new MutationCache({ onError }),
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
}
