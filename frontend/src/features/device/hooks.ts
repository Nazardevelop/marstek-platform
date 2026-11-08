import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { PatchDevice } from '@/api/types';
import * as api from './api';

export const deviceKeys = {
  all: ['devices'] as const,
  list: () => [...deviceKeys.all, 'list'] as const,
  detail: (id: number) => [...deviceKeys.all, id, 'detail'] as const,
  status: (id: number) => [...deviceKeys.all, id, 'status'] as const,
  mode: (id: number) => [...deviceKeys.all, id, 'mode'] as const,
  network: (id: number) => [...deviceKeys.all, id, 'network'] as const,
};

export const STATUS_POLL_MS = 10_000;

export function useDevices() {
  return useQuery({ queryKey: deviceKeys.list(), queryFn: api.listDevices });
}

/**
 * The device the UI works with. Single device for now: the first registered one.
 * The list only has stored info; the detail endpoint re-reads model/firmware, so capabilities
 * come from there (falling back to the list entry while it loads or if the device is offline).
 * Kept as its own hook so multi-device support only needs to change this.
 */
export function useCurrentDevice() {
  const devices = useDevices();
  const id = devices.data?.[0]?.id;
  const detail = useQuery({
    queryKey: deviceKeys.detail(id ?? -1),
    queryFn: () => api.getDevice(id as number),
    enabled: id !== undefined,
    staleTime: 60_000,
  });
  return { ...devices, device: detail.data ?? devices.data?.[0] };
}

export function useStatus(id: number | undefined) {
  return useQuery({
    queryKey: deviceKeys.status(id ?? -1),
    queryFn: () => api.getStatus(id as number),
    enabled: id !== undefined,
    refetchInterval: STATUS_POLL_MS,
  });
}

export function useMode(id: number | undefined) {
  return useQuery({
    queryKey: deviceKeys.mode(id ?? -1),
    queryFn: () => api.getMode(id as number),
    enabled: id !== undefined,
    refetchInterval: STATUS_POLL_MS,
  });
}

export function useNetwork(id: number | undefined) {
  return useQuery({
    queryKey: deviceKeys.network(id ?? -1),
    queryFn: () => api.getNetwork(id as number),
    enabled: id !== undefined,
  });
}

export function usePatchDevice(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PatchDevice) => api.patchDevice(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: deviceKeys.all }),
  });
}

export function useDiscoverDevices() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.discoverDevices,
    onSuccess: () => qc.invalidateQueries({ queryKey: deviceKeys.all }),
  });
}
