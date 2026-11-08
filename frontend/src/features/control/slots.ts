import type { ManualSlot, Weekday } from '@/api/types';

export const WEEKDAYS: { value: Weekday; label: string }[] = [
  { value: 'mon', label: 'Mon' },
  { value: 'tue', label: 'Tue' },
  { value: 'wed', label: 'Wed' },
  { value: 'thu', label: 'Thu' },
  { value: 'fri', label: 'Fri' },
  { value: 'sat', label: 'Sat' },
  { value: 'sun', label: 'Sun' },
];

export const MAX_POWER_W = 2500;

export function newSlot(existing: ManualSlot[], withAction: boolean): ManualSlot {
  const used = new Set(existing.map((s) => s.index));
  let index = 0;
  while (used.has(index)) index++;
  return {
    index,
    start: '08:00',
    end: '20:00',
    weekdays: WEEKDAYS.map((d) => d.value),
    power_w: 100,
    enabled: true,
    ...(withAction ? { action: 'charge' as const } : {}),
  };
}

/** Client-side check that mirrors the backend rules, so the user sees errors before confirming. */
export function slotError(s: ManualSlot): string | null {
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(s.start) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(s.end)) {
    return 'Use 24h hh:mm times';
  }
  if (s.start === s.end) return 'End time must differ from start';
  if (s.enabled && s.weekdays.length === 0) return 'Pick at least one day';
  if (!Number.isInteger(s.power_w) || Math.abs(s.power_w) > MAX_POWER_W) {
    return `Power must be a whole number between -${MAX_POWER_W} and ${MAX_POWER_W} W`;
  }
  return null;
}
