import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import type { ReactNode } from 'react';
import { Link } from 'react-router';
import type { Device } from '@/api/types';
import { QueryState } from '@/components/QueryState';
import { useCurrentDevice } from '../hooks';

type Props = { children: (device: Device) => ReactNode };

/** Renders children only once a device is known; otherwise loading/error/empty state. */
export function RequireDevice({ children }: Props) {
  const { device, isPending, error } = useCurrentDevice();
  if (isPending || error) return <QueryState isPending={isPending} error={error} label="devices" />;
  if (!device) {
    return (
      <Alert
        severity="info"
        action={
          <Button component={Link} to="/settings" color="inherit" size="small">
            Find devices
          </Button>
        }
      >
        No device registered yet. Run discovery in Settings.
      </Alert>
    );
  }
  return <>{children(device)}</>;
}
