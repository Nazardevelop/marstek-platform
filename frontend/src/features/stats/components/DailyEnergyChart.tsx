import { BarChart } from '@mui/x-charts/BarChart';
import { QueryState } from '@/components/QueryState';
import { StatCard } from '@/components/StatCard';
import { useDailyEnergy } from '../hooks';

type Props = { deviceId: number; days: number };

const kwh = (wh: number | null) => (wh == null ? null : Math.round(wh / 10) / 100);

export function DailyEnergyChart({ deviceId, days }: Props) {
  const { data, isPending, error } = useDailyEnergy(deviceId, days);
  return (
    <StatCard title={`Daily energy (kWh), last ${days} days`}>
      {!data ? (
        <QueryState isPending={isPending} error={error} label="daily energy" />
      ) : data.length === 0 ? (
        'No energy data recorded yet.'
      ) : (
        <BarChart
          height={280}
          xAxis={[
            {
              data: data.map((d) => d.date),
              scaleType: 'band',
              valueFormatter: (v: string) =>
                new Date(`${v}T00:00`).toLocaleDateString(undefined, {
                  day: 'numeric',
                  month: 'short',
                }),
            },
          ]}
          series={[
            { data: data.map((d) => kwh(d.pv_wh)), label: 'Solar' },
            { data: data.map((d) => kwh(d.load_wh)), label: 'Load' },
            { data: data.map((d) => kwh(d.grid_import_wh)), label: 'Grid import' },
            { data: data.map((d) => kwh(d.grid_export_wh)), label: 'Grid export' },
          ]}
        />
      )}
    </StatCard>
  );
}
