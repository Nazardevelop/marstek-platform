import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import type { PvInput } from '@/api/types';
import { StatCard } from '@/components/StatCard';
import { formatNumber, formatWatts } from '@/lib/format';

export function PvCard({ inputs }: { inputs: PvInput[] }) {
  return (
    <StatCard title="Solar inputs">
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
        {inputs.map((pv) => (
          <Box key={pv.input} sx={{ p: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle2">PV{pv.input}</Typography>
              <Chip
                size="small"
                label={pv.active ? 'Working' : 'Standby'}
                color={pv.active ? 'success' : 'default'}
              />
            </Box>
            <Typography sx={{ fontWeight: 600 }}>{formatWatts(pv.power_w)}</Typography>
            <Typography variant="caption" color="text.secondary">
              {formatNumber(pv.voltage_v, 'V')} · {formatNumber(pv.current_a, 'A', 2)}
            </Typography>
          </Box>
        ))}
      </Box>
    </StatCard>
  );
}
