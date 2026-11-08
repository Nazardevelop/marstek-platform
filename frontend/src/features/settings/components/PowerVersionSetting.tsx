import Button from '@mui/material/Button';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import { useState } from 'react';
import type { PowerWatts } from '@/api/types';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { WriteResult } from '@/components/WriteResult';
import { useSetPowerVersion } from '../hooks';
import { SettingRow } from './SettingRow';

const OPTIONS: PowerWatts[] = [800, 1200, 1500, 2200, 2500];

export function PowerVersionSetting({ deviceId }: { deviceId: number }) {
  const m = useSetPowerVersion(deviceId);
  const [watts, setWatts] = useState<PowerWatts>(800);
  const [confirming, setConfirming] = useState(false);
  return (
    <SettingRow
      title="Power version"
      description="Maximum charge/discharge power rating. Only change this if you know your model's rating."
      result={<WriteResult {...m} setResult={m.data?.set_result} />}
    >
      <TextField
        select
        size="small"
        label="Power"
        value={watts}
        onChange={(e) => setWatts(Number(e.target.value) as PowerWatts)}
        sx={{ width: 130 }}
      >
        {OPTIONS.map((w) => (
          <MenuItem key={w} value={w}>
            {w} W
          </MenuItem>
        ))}
      </TextField>
      <Button
        variant="outlined"
        color="warning"
        disabled={m.isPending}
        onClick={() => setConfirming(true)}
      >
        Set
      </Button>
      <ConfirmDialog
        open={confirming}
        danger
        title={`Set power version to ${watts} W?`}
        onClose={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          m.mutate(watts);
        }}
      >
        A wrong rating can make the device charge or discharge outside its limits. This sends{' '}
        <code>Set.Ver</code>.
      </ConfirmDialog>
    </SettingRow>
  );
}
