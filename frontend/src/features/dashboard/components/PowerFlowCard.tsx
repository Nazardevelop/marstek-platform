import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { Status } from '@/api/types';
import { StatCard } from '@/components/StatCard';
import { formatWatts } from '@/lib/format';

type Props = { power: Status['power'] };

// Sign conventions from the device: positive battery_w = discharging, positive grid_w = feeding the grid.
// (The spec doesn't state them explicitly; adjust here if the real device disagrees.)
function direction(w: number | null, pos: string, neg: string): string {
  if (w == null || Math.abs(w) < 1) return 'Idle';
  return w > 0 ? pos : neg;
}

export function PowerFlowCard({ power }: Props) {
  const rows = [
    { label: 'Solar', value: power.pv_w, note: power.pv_w ? 'Producing' : 'Idle' },
    {
      label: 'Battery',
      value: power.battery_w,
      note: direction(power.battery_w, 'Discharging', 'Charging'),
    },
    { label: 'Grid', value: power.grid_w, note: direction(power.grid_w, 'Exporting', 'Importing') },
    {
      label: 'Off-grid load',
      value: power.offgrid_w,
      note: power.offgrid_w ? 'Supplying' : 'Idle',
    },
  ];
  return (
    <StatCard title="Power flow">
      <Box
        component="dl"
        sx={{
          m: 0,
          display: 'grid',
          gridTemplateColumns: 'auto 1fr auto',
          rowGap: 1.25,
          columnGap: 2,
        }}
      >
        {rows.map((r) => (
          <Box key={r.label} sx={{ display: 'contents' }}>
            <Typography component="dt" color="text.secondary">
              {r.label}
            </Typography>
            <Typography
              component="dd"
              variant="caption"
              color="text.secondary"
              sx={{ m: 0, alignSelf: 'center' }}
            >
              {r.note}
            </Typography>
            <Typography component="dd" sx={{ m: 0, fontWeight: 600, textAlign: 'right' }}>
              {formatWatts(r.value == null ? null : Math.abs(r.value))}
            </Typography>
          </Box>
        ))}
      </Box>
    </StatCard>
  );
}
