import Button from '@mui/material/Button';
import { useState } from 'react';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { WriteResult } from '@/components/WriteResult';
import { useSetBleAdv, useSetLed } from '../hooks';
import { SettingRow } from './SettingRow';

type ToggleProps = {
  title: string;
  description: string;
  method: string;
  mutation: ReturnType<typeof useSetLed>;
};

function ToggleSetting({ title, description, method, mutation: m }: ToggleProps) {
  const [pending, setPending] = useState<boolean | null>(null);
  return (
    <SettingRow
      title={title}
      description={description}
      result={<WriteResult {...m} setResult={m.data?.set_result} />}
    >
      <Button variant="outlined" disabled={m.isPending} onClick={() => setPending(true)}>
        Turn on
      </Button>
      <Button variant="outlined" disabled={m.isPending} onClick={() => setPending(false)}>
        Turn off
      </Button>
      <ConfirmDialog
        open={pending !== null}
        title={`Turn ${title.toLowerCase()} ${pending ? 'on' : 'off'}?`}
        onClose={() => setPending(null)}
        onConfirm={() => {
          if (pending !== null) m.mutate(pending);
          setPending(null);
        }}
      >
        This sends <code>{method}</code> to the device.
      </ConfirmDialog>
    </SettingRow>
  );
}

export function LedSetting({ deviceId }: { deviceId: number }) {
  return (
    <ToggleSetting
      title="Panel LEDs"
      description="The lights on the device."
      method="Led.Ctrl"
      mutation={useSetLed(deviceId)}
    />
  );
}

export function BleSetting({ deviceId }: { deviceId: number }) {
  return (
    <ToggleSetting
      title="Bluetooth advertising"
      description="Turning it off hides the device from Bluetooth pairing (Bluetooth lock)."
      method="Ble.Adv"
      mutation={useSetBleAdv(deviceId)}
    />
  );
}
