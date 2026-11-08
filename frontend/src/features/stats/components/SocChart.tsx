import { LineChart } from '@mui/x-charts/LineChart';
import type { HistoryRange } from '@/api/types';
import { QueryState } from '@/components/QueryState';
import { StatCard } from '@/components/StatCard';
import { useHistory } from '../hooks';
import { timeFormatter, toDates } from './chartUtils';

type Props = { deviceId: number; range: HistoryRange };

export function SocChart({ deviceId, range }: Props) {
  const { data, isPending, error } = useHistory(deviceId, range);
  return (
    <StatCard title="Battery state of charge">
      {!data ? (
        <QueryState isPending={isPending} error={error} label="history" />
      ) : data.points.length === 0 ? (
        'No history recorded yet.'
      ) : (
        <LineChart
          height={240}
          xAxis={[
            { data: toDates(data.points), scaleType: 'time', valueFormatter: timeFormatter(range) },
          ]}
          yAxis={[{ min: 0, max: 100, valueFormatter: (v: number) => `${v}%` }]}
          series={[
            {
              data: data.points.map((p) => p.soc_pct ?? null),
              label: 'SOC %',
              area: true,
              showMark: false,
            },
          ]}
        />
      )}
    </StatCard>
  );
}
