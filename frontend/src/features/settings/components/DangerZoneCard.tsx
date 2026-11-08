import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useState } from 'react';
import type { Device, FactoryResetType } from '@/api/types';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { WriteResult } from '@/components/WriteResult';
import { useFactoryReset } from '../hooks';

export function DangerZoneCard({ device }: { device: Device }) {
  const reset = useFactoryReset(device.id);
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<FactoryResetType>(2);
  const [typed, setTyped] = useState('');

  const close = () => {
    setOpen(false);
    setTyped('');
  };

  return (
    <Card variant="outlined" sx={{ borderColor: 'error.main' }}>
      <CardContent>
        <Typography component="h2" variant="subtitle2" color="error" gutterBottom>
          Danger zone
        </Typography>
        <Typography gutterBottom>
          Factory reset erases all device settings. You'll need to set it up again in the Marstek
          app.
        </Typography>
        <Button
          color="error"
          variant="outlined"
          disabled={reset.isPending}
          onClick={() => setOpen(true)}
        >
          Factory reset…
        </Button>
        <WriteResult
          {...reset}
          setResult={reset.data?.set_result}
          successText="Reset command accepted."
        />
        <ConfirmDialog
          open={open}
          danger
          title="Factory reset the device?"
          confirmLabel="Reset device"
          confirmDisabled={typed !== device.name}
          onClose={close}
          onConfirm={() => {
            reset.mutate({ type, confirmName: typed });
            close();
          }}
        >
          <Alert severity="error" sx={{ mb: 2 }}>
            This can't be undone.
          </Alert>
          <RadioGroup
            value={type}
            onChange={(e) => setType(Number(e.target.value) as FactoryResetType)}
          >
            <FormControlLabel value={2} control={<Radio />} label="Reset, keep energy history" />
            <FormControlLabel
              value={1}
              control={<Radio />}
              label="Reset and clear energy history"
            />
          </RadioGroup>
          <TextField
            fullWidth
            margin="normal"
            label={`Type "${device.name}" to confirm`}
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            autoComplete="off"
          />
        </ConfirmDialog>
      </CardContent>
    </Card>
  );
}
