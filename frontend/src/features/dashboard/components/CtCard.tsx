import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import type { Status } from '@/api/types';
import { Metric } from '@/components/Metric';
import { StatCard } from '@/components/StatCard';
import { formatWatts, formatWh } from '@/lib/format';

export function CtCard({ ct }: { ct: Status['ct'] }) {
  return (
    <StatCard title="Energy meter (CT)">
      {!ct.connected ? (
        <Alert severity="info">CT not connected.</Alert>
      ) : (
        <>
          <Metric label="Total" value={formatWatts(ct.total_w)} big />
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1.5, my: 1.5 }}>
            <Metric label="Phase A" value={formatWatts(ct.phase_a_w)} />
            <Metric label="Phase B" value={formatWatts(ct.phase_b_w)} />
            <Metric label="Phase C" value={formatWatts(ct.phase_c_w)} />
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
            <Metric label="Imported (total)" value={formatWh(ct.import_wh)} />
            <Metric label="Exported (total)" value={formatWh(ct.export_wh)} />
          </Box>
        </>
      )}
    </StatCard>
  );
}
