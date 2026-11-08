import { LineChart } from '@mui/x-charts/LineChart';
import type { HistoryRange } from '@/api/types';
import { QueryState } from '@/components/QueryState';
import { StatCard } from '@/components/StatCard';
import { useHistory } from '../hooks';
import { timeFormatter, toDates } from './chartUtils';

type Props = { deviceId: number; range: HistoryRange };

const SERIES = [
  { key: 'pv_w', label: 'Solar' },
  { key: 'battery_w', label: 'Battery' },
  { key: 'grid_w', label: 'Grid' },
  { key: 'offgrid_w', label: 'Off-grid' },
] as const;

export function PowerChart({ deviceId, range }: Props) {
  const { data, isPending, error } = useHistory(deviceId, range);
  return (
    <StatCard title="Power (W)">
      {!data ? (
        <QueryState isPending={isPending} error={error} label="history" />
      ) : data.points.length === 0 ? (
        'No history recorded yet.'
      ) : (
        <LineChart
          height={280}
          xAxis={[
            { data: toDates(data.points), scaleType: 'time', valueFormatter: timeFormatter(range) },
          ]}
          series={SERIES.map((s) => ({
            data: data.points.map((p) => p[s.key] ?? null),
            label: s.label,
            showMark: false,
            valueFormatter: (v: number | null) => (v == null ? '—' : `${Math.round(v)} W`),
          }))}
        />
      )}
    </StatCard>
  );
}
