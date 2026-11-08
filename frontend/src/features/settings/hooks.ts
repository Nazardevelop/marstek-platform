import { useMutation } from '@tanstack/react-query';
import type { FactoryResetType, PowerWatts } from '@/api/types';
import * as api from '@/features/device/api';

// ⚠️ All of these change real hardware. The device has no "read" for these settings,
// so there's nothing to invalidate; the UI shows the write result instead.
export const useSetDod = (id: number) =>
  useMutation({ mutationFn: (v: number) => api.setDod(id, v) });
export const useSetLed = (id: number) =>
  useMutation({ mutationFn: (on: boolean) => api.setLed(id, on) });
export const useSetBleAdv = (id: number) =>
  useMutation({ mutationFn: (on: boolean) => api.setBleAdv(id, on) });
export const useSetPowerVersion = (id: number) =>
  useMutation({ mutationFn: (w: PowerWatts) => api.setPowerVersion(id, w) });
export const useFactoryReset = (id: number) =>
  useMutation({
    mutationFn: ({ type, confirmName }: { type: FactoryResetType; confirmName: string }) =>
      api.factoryReset(id, type, confirmName),
  });
