import type { HistoryPoint, HistoryRange } from '@/api/types';

export function toDates(points: HistoryPoint[]): Date[] {
  return points.map((p) => new Date(p.t));
}

export function timeFormatter(range: HistoryRange) {
  return (d: Date) =>
    range === '24h'
      ? d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}
