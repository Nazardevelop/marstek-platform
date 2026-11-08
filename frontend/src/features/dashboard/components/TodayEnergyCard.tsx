import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import { Link } from 'react-router';
import { Metric } from '@/components/Metric';
import { QueryState } from '@/components/QueryState';
import { StatCard } from '@/components/StatCard';
import { useDailyEnergy } from '@/features/stats/hooks';
import { formatWh } from '@/lib/format';

export function TodayEnergyCard({ deviceId }: { deviceId: number }) {
  const { data, isPending, error } = useDailyEnergy(deviceId, 1);
  const today = data?.at(-1);
  return (
    <StatCard
      title="Today"
      action={
        <Button component={Link} to="/stats" size="small">
          History
        </Button>
      }
    >
      {!data ? (
        <QueryState isPending={isPending} error={error} label="today's energy" />
      ) : !today ? (
        <Box sx={{ color: 'text.secondary' }}>No data recorded yet today.</Box>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
          <Metric label="Solar" value={formatWh(today.pv_wh)} />
          <Metric label="Load" value={formatWh(today.load_wh)} />
          <Metric label="Grid import" value={formatWh(today.grid_import_wh)} />
          <Metric label="Grid export" value={formatWh(today.grid_export_wh)} />
        </Box>
      )}
    </StatCard>
  );
}
