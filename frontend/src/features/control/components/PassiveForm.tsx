import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useState } from 'react';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { formatWatts } from '@/lib/format';
import { useSetMode } from '../hooks';
import { MAX_POWER_W } from '../slots';
import { ModeWriteFeedback } from './ModeWriteFeedback';

const MAX_COUNTDOWN_S = 86_400;

export function PassiveForm({ deviceId }: { deviceId: number }) {
  const setMode = useSetMode(deviceId);
  const [power, setPower] = useState('300');
  const [minutes, setMinutes] = useState('5');
  const [confirming, setConfirming] = useState(false);

  const powerW = Number(power);
  const countdownS = Math.round(Number(minutes) * 60);
  const powerError =
    power === '' || !Number.isInteger(powerW) || Math.abs(powerW) > MAX_POWER_W
      ? `Whole number, -${MAX_POWER_W} to ${MAX_POWER_W}`
      : null;
  const timeError =
    minutes === '' || !(countdownS >= 1 && countdownS <= MAX_COUNTDOWN_S)
      ? 'Between 1 s and 24 h'
      : null;

  return (
    <>
      <Typography gutterBottom>
        Run at a fixed power, then stop after the countdown. The spec doesn't define the power sign;
        check on your device which direction is charging.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', my: 2 }}>
        <TextField
          label="Power (W)"
          type="number"
          value={power}
          onChange={(e) => setPower(e.target.value)}
          error={!!powerError}
          helperText={powerError ?? ' '}
        />
        <TextField
          label="Countdown (minutes)"
          type="number"
          value={minutes}
          onChange={(e) => setMinutes(e.target.value)}
          error={!!timeError}
          helperText={timeError ?? ' '}
          slotProps={{ htmlInput: { step: 'any', min: 0 } }}
        />
      </Box>
      <Button
        variant="contained"
        disabled={!!powerError || !!timeError || setMode.isPending}
        onClick={() => setConfirming(true)}
      >
        {setMode.isPending ? 'Applying…' : 'Activate Passive'}
      </Button>
      <ModeWriteFeedback data={setMode.data} error={setMode.error} isError={setMode.isError} />
      <ConfirmDialog
        open={confirming}
        title="Switch to Passive?"
        confirmLabel="Switch mode"
        onClose={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          setMode.mutate({ mode: 'passive', power_w: powerW, countdown_s: countdownS });
        }}
      >
        Power {formatWatts(powerW)} for {minutes} min ({countdownS} s).
      </ConfirmDialog>
    </>
  );
}
