import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Box from '@mui/material/Box';
import { useSearchParams } from 'react-router';
import type { HistoryRange } from '@/api/types';
import { PageTitle } from '@/components/PageTitle';
import { RequireDevice } from '@/features/device/components/RequireDevice';
import { DailyEnergyChart } from './components/DailyEnergyChart';
import { PowerChart } from './components/PowerChart';
import { SocChart } from './components/SocChart';

const RANGES: { value: HistoryRange; label: string; days: number }[] = [
  { value: '24h', label: '24 h', days: 1 },
  { value: '7d', label: '7 days', days: 7 },
  { value: '30d', label: '30 days', days: 30 },
];

function isRange(v: string | null): v is HistoryRange {
  return RANGES.some((r) => r.value === v);
}

export function StatsPage() {
  // The range lives in the URL (?range=7d): shareable, survives reload, and the assistant sees it as context.
  const [params, setParams] = useSearchParams();
  const raw = params.get('range');
  const range: HistoryRange = isRange(raw) ? raw : '24h';
  const days = RANGES.find((r) => r.value === range)?.days ?? 1;

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
        }}
      >
        <PageTitle>Statistics</PageTitle>
        <ToggleButtonGroup
          exclusive
          size="small"
          value={range}
          onChange={(_, v: HistoryRange | null) => v && setParams({ range: v })}
          aria-label="Time range"
          sx={{ mb: 2 }}
        >
          {RANGES.map((r) => (
            <ToggleButton key={r.value} value={r.value}>
              {r.label}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>
      <RequireDevice>
        {(device) => (
          <Box sx={{ display: 'grid', gap: 2 }}>
            <SocChart deviceId={device.id} range={range} />
            <PowerChart deviceId={device.id} range={range} />
            <DailyEnergyChart deviceId={device.id} days={Math.max(days, 7)} />
          </Box>
        )}
      </RequireDevice>
    </>
  );
}
