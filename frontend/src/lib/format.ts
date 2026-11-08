const dash = '—';

export function formatWatts(w: number | null | undefined): string {
  if (w == null) return dash;
  return Math.abs(w) >= 1000 ? `${(w / 1000).toFixed(2)} kW` : `${Math.round(w)} W`;
}

export function formatWh(wh: number | null | undefined): string {
  if (wh == null) return dash;
  return Math.abs(wh) >= 1000 ? `${(wh / 1000).toFixed(2)} kWh` : `${Math.round(wh)} Wh`;
}

export function formatPct(pct: number | null | undefined): string {
  return pct == null ? dash : `${Math.round(pct)}%`;
}

export function formatNumber(n: number | null | undefined, unit: string, digits = 1): string {
  return n == null ? dash : `${n.toFixed(digits)} ${unit}`;
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return dash;
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'medium' });
}

export const MODE_LABELS = {
  auto: 'Auto',
  ai: 'AI',
  manual: 'Manual',
  passive: 'Passive',
  ups: 'UPS',
} as const;

export function modeLabel(mode: keyof typeof MODE_LABELS | null | undefined): string {
  return mode ? MODE_LABELS[mode] : 'Unknown';
}
