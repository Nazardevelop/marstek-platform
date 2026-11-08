import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { SetModeRequest } from '@/api/types';
import { setMode } from '@/features/device/api';
import { deviceKeys } from '@/features/device/hooks';

/** ⚠️ Changes real hardware. No optimistic update: wait for the device, then refetch. */
export function useSetMode(deviceId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SetModeRequest) => setMode(deviceId, body),
    onSettled: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: deviceKeys.mode(deviceId) }),
        qc.invalidateQueries({ queryKey: deviceKeys.status(deviceId) }),
      ]),
  });
}
