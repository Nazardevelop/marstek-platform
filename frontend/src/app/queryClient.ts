import { QueryClient } from '@tanstack/react-query';
import { ApiError } from '@/api/http';

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5_000,
        // Don't hammer the device: one retry, and none for client errors (4xx).
        retry: (count, err) => !(err instanceof ApiError && err.status < 500) && count < 1,
      },
      mutations: { retry: false }, // never auto-retry hardware writes
    },
  });
}
