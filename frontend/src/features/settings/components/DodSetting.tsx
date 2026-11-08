import Button from '@mui/material/Button';
import Slider from '@mui/material/Slider';
import { useState } from 'react';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { WriteResult } from '@/components/WriteResult';
import { useSetDod } from '../hooks';
import { SettingRow } from './SettingRow';

const DOD_MIN = 30;
const DOD_MAX = 88;

export function DodSetting({ deviceId }: { deviceId: number }) {
  const m = useSetDod(deviceId);
  const [value, setValue] = useState(DOD_MAX);
  const [confirming, setConfirming] = useState(false);
  return (
    <SettingRow
      title="Depth of discharge"
      description={`How much of the battery may be used (${DOD_MIN}–${DOD_MAX}%, default ${DOD_MAX}%).`}
      result={<WriteResult {...m} setResult={m.data?.set_result} />}
    >
      <Slider
        aria-label="Depth of discharge"
        min={DOD_MIN}
        max={DOD_MAX}
        value={value}
        onChange={(_, v) => setValue(v as number)}
        valueLabelDisplay="auto"
        sx={{ width: 160 }}
      />
      <Button variant="outlined" disabled={m.isPending} onClick={() => setConfirming(true)}>
        Set {value}%
      </Button>
      <ConfirmDialog
        open={confirming}
        title={`Set depth of discharge to ${value}%?`}
        onClose={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          m.mutate(value);
        }}
      >
        This sends <code>DOD.SET</code> to the device.
      </ConfirmDialog>
    </SettingRow>
  );
}
