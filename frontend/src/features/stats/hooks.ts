import { keepPreviousData, useQuery } from '@tanstack/react-query';
import type { HistoryRange } from '@/api/types';
import { getDailyEnergy, getHistory } from './api';

export const statsKeys = {
  history: (id: number, range: HistoryRange) => ['devices', id, 'history', range] as const,
  daily: (id: number, days: number) => ['devices', id, 'energy-daily', days] as const,
};

export function useHistory(id: number, range: HistoryRange) {
  return useQuery({
    queryKey: statsKeys.history(id, range),
    queryFn: () => getHistory(id, range),
    placeholderData: keepPreviousData, // keep the old chart while switching range
    refetchInterval: 60_000,
  });
}

export function useDailyEnergy(id: number, days: number) {
  return useQuery({
    queryKey: statsKeys.daily(id, days),
    queryFn: () => getDailyEnergy(id, days),
    refetchInterval: 60_000,
  });
}
