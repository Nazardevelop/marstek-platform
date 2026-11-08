# Data fetching

Layers (each one replaceable/mocked in tests):
```
component → feature hook (useQuery/useMutation) → api client function → http helper → Django /api
```

## HTTP helper (`src/api/http.ts`)
```ts
export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;
  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}
// No `constructor(public x)` parameter properties or `enum`s: Vite's tsconfig enables
// `erasableSyntaxOnly`, which rejects TS-only runtime syntax. Use `as const` objects instead of enums.

const BASE = import.meta.env.VITE_API_URL ?? '/api';

export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => undefined);
    throw new ApiError(res.status, `HTTP ${res.status} for ${path}`, body);
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
}
```
- Use a Vite dev proxy (`server.proxy['/api']`) instead of hardcoding the backend host / fighting CORS.

## DTO types (`src/api/types.ts` or per feature)
Mirror the Django serializer output exactly (snake_case is fine; don't rename in random places).
If you need a UI-friendly shape, map it in the API function, once.
Validate at the boundary with zod if data is untrusted or the contract is unstable.

## API functions (`src/features/<feature>/api.ts`)
```ts
export const getBatteryStatus = (deviceId: string) =>
  http<BatteryStatus>(`/devices/${deviceId}/battery/`);

export const setMode = (deviceId: string, body: SetModeRequest) =>
  http<SetModeResponse>(`/devices/${deviceId}/mode/`, { method: 'POST', body: JSON.stringify(body) });
```

## Query keys & hooks
```ts
export const deviceKeys = {
  all: ['devices'] as const,
  battery: (id: string) => [...deviceKeys.all, id, 'battery'] as const,
  mode: (id: string) => [...deviceKeys.all, id, 'mode'] as const,
};

export function useBatteryStatus(id: string) {
  return useQuery({
    queryKey: deviceKeys.battery(id),
    queryFn: () => getBatteryStatus(id),
    refetchInterval: 10_000,     // live data: poll; don't hand-roll setInterval + fetch
  });
}

export function useSetMode(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SetModeRequest) => setMode(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: deviceKeys.mode(id) }),
  });
}
```
- One `QueryClient` created at the app root (`QueryClientProvider`), not per component.
- Use `isPending` / `isError` / `error` from the hook; render all three states.

## Write (hardware) commands
- Confirmation step before `mutate` (dialog stating what will change).
- `disabled={mutation.isPending}` on the trigger; show success/error after.
- No optimistic updates for device writes — wait for the device to confirm, then invalidate.
- Never expose factory reset in a casual place; require typing a confirmation word.
