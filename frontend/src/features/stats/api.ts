import { http } from '@/api/http';
import type { DailyEnergy, History, HistoryRange } from '@/api/types';

export const HISTORY_METRICS = ['soc_pct', 'battery_w', 'pv_w', 'grid_w', 'offgrid_w'] as const;

export const getHistory = (id: number, range: HistoryRange) =>
  http<History>(`/devices/${id}/history/?range=${range}&metrics=${HISTORY_METRICS.join(',')}`);

export const getDailyEnergy = (id: number, days: number) =>
  http<DailyEnergy[]>(`/devices/${id}/energy/daily/?days=${days}`);
