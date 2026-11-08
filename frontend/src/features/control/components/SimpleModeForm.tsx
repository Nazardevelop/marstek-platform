import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { useState } from 'react';
import type { Mode } from '@/api/types';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { modeLabel } from '@/lib/format';
import { useSetMode } from '../hooks';
import { ModeWriteFeedback } from './ModeWriteFeedback';

type Props = { deviceId: number; mode: Exclude<Mode, 'manual' | 'passive'>; isCurrent: boolean };

/** Auto / AI / UPS: no settings, just switch. */
export function SimpleModeForm({ deviceId, mode, isCurrent }: Props) {
  const setMode = useSetMode(deviceId);
  const [confirming, setConfirming] = useState(false);

  return (
    <>
      <Typography gutterBottom>
        {isCurrent
          ? `${modeLabel(mode)} is already active.`
          : `Switch the device to ${modeLabel(mode)} mode.`}
      </Typography>
      <Button variant="contained" disabled={setMode.isPending} onClick={() => setConfirming(true)}>
        {setMode.isPending ? 'Applying…' : `Activate ${modeLabel(mode)}`}
      </Button>
      <ModeWriteFeedback data={setMode.data} error={setMode.error} isError={setMode.isError} />
      <ConfirmDialog
        open={confirming}
        title={`Switch to ${modeLabel(mode)}?`}
        confirmLabel="Switch mode"
        onClose={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          setMode.mutate({ mode });
        }}
      >
        This sends <code>ES.SetMode</code> to the device.
      </ConfirmDialog>
    </>
  );
}
