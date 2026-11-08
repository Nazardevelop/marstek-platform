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

export const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

/** Pull a human-readable message out of the backend's error envelope, if there is one. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const body = err.body;
    if (body && typeof body === 'object') {
      const b = body as Record<string, unknown>;
      const nested =
        b.error && typeof b.error === 'object' ? (b.error as Record<string, unknown>) : b;
      if (typeof nested.message === 'string') return nested.message;
      if (typeof nested.detail === 'string') return nested.detail;
    }
    return err.message;
  }
  return err instanceof Error ? err.message : 'Unknown error';
}

export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    const body: unknown = await res.json().catch(() => undefined);
    throw new ApiError(res.status, `HTTP ${res.status} for ${path}`, body);
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
}

export const postJson = <T>(path: string, body?: unknown) =>
  http<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });
