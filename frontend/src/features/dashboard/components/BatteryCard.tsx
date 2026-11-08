import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import type { Status } from '@/api/types';
import { Metric } from '@/components/Metric';
import { StatCard } from '@/components/StatCard';
import { formatNumber, formatPct, formatWh } from '@/lib/format';

type Props = { battery: Status['battery']; systemSocPct: number | null };

export function BatteryCard({ battery, systemSocPct }: Props) {
  const soc = battery.soc_pct ?? systemSocPct;
  return (
    <StatCard title="Battery">
      <Metric label="State of charge" value={formatPct(soc)} big />
      <LinearProgress
        variant="determinate"
        value={soc ?? 0}
        aria-label="State of charge"
        sx={{ height: 10, borderRadius: 5, my: 1.5 }}
        color={soc != null && soc < 20 ? 'warning' : 'primary'}
      />
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5, mb: 1.5 }}>
        <Metric label="Remaining" value={formatWh(battery.remaining_wh)} />
        <Metric label="Rated" value={formatWh(battery.rated_wh)} />
        <Metric label="Temperature" value={formatNumber(battery.temperature_c, '°C')} />
      </Box>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip
          size="small"
          label={battery.charge_allowed ? 'Charging allowed' : 'Charging blocked'}
          color={battery.charge_allowed ? 'success' : 'default'}
        />
        <Chip
          size="small"
          label={battery.discharge_allowed ? 'Discharging allowed' : 'Discharging blocked'}
          color={battery.discharge_allowed ? 'success' : 'default'}
        />
      </Box>
    </StatCard>
  );
}
