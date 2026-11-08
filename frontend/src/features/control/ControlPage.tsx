import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import { useState } from 'react';
import type { Device, Mode } from '@/api/types';
import { PageTitle } from '@/components/PageTitle';
import { QueryState } from '@/components/QueryState';
import { RequireDevice } from '@/features/device/components/RequireDevice';
import { useMode } from '@/features/device/hooks';
import { MODE_LABELS, modeLabel } from '@/lib/format';
import { ManualForm } from './components/ManualForm';
import { PassiveForm } from './components/PassiveForm';
import { SimpleModeForm } from './components/SimpleModeForm';

const MODES = Object.keys(MODE_LABELS) as Mode[];

const DESCRIPTIONS: Record<Mode, string> = {
  auto: 'The device balances your home consumption using the CT meter.',
  ai: 'The device optimizes charging and discharging automatically.',
  manual: 'Fixed charge/discharge power in scheduled time slots.',
  passive: 'Charge or discharge at a fixed power for a limited time.',
  ups: 'Keep the battery as a backup power supply.',
};

function Control({ device }: { device: Device }) {
  const mode = useMode(device.id);
  const [selected, setSelected] = useState<Mode | null>(null);
  const current = mode.data?.mode ?? null;
  const shown = selected ?? current ?? 'auto';

  return (
    <Box sx={{ display: 'grid', gap: 2, maxWidth: 760 }}>
      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle2" color="text.secondary">
            Current mode
          </Typography>
          {mode.data ? (
            <Typography variant="h5" component="p">
              {modeLabel(current)}
              {mode.data.stale && (
                <Typography component="span" color="warning.main" sx={{ ml: 1 }}>
                  (last known)
                </Typography>
              )}
            </Typography>
          ) : (
            <QueryState isPending={mode.isPending} error={mode.error} label="mode" />
          )}
        </CardContent>
      </Card>

      <Box>
        <Typography component="h2" variant="subtitle1" gutterBottom>
          Choose a mode
        </Typography>
        <ToggleButtonGroup
          exclusive
          value={shown}
          onChange={(_, v: Mode | null) => v && setSelected(v)}
          aria-label="Mode"
          sx={{ flexWrap: 'wrap' }}
        >
          {MODES.map((m) => (
            <ToggleButton key={m} value={m} sx={{ px: 2.5 }}>
              {MODE_LABELS[m]}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {DESCRIPTIONS[shown]}
        </Typography>
      </Box>

      <Card variant="outlined">
        <CardContent>
          {shown === 'passive' ? (
            <PassiveForm deviceId={device.id} />
          ) : shown === 'manual' ? (
            <ManualForm
              deviceId={device.id}
              maxSlots={device.capabilities.manual_slots}
              withAction={device.capabilities.manual_action}
            />
          ) : (
            <SimpleModeForm deviceId={device.id} mode={shown} isCurrent={shown === current} />
          )}
        </CardContent>
      </Card>

      <Alert severity="info" variant="outlined">
        Changing the mode sends a command to the real device. You'll be asked to confirm first.
      </Alert>
    </Box>
  );
}

export function ControlPage() {
  return (
    <>
      <PageTitle>Control</PageTitle>
      <RequireDevice>{(device) => <Control device={device} />}</RequireDevice>
    </>
  );
}
