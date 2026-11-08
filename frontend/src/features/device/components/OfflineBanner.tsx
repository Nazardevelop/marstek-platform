import Alert from '@mui/material/Alert';
import { formatTime } from '@/lib/format';
import { useCurrentDevice, useStatus } from '../hooks';

/** Shown on every page when the device is unreachable; values on screen are last-known. */
export function OfflineBanner() {
  const { device } = useCurrentDevice();
  const status = useStatus(device?.id);
  if (!status.data?.stale && !status.isError) return null;
  return (
    <Alert severity="warning" sx={{ mb: 2 }}>
      {status.data
        ? `Device unreachable. Showing last-known values from ${formatTime(status.data.fetched_at)}.`
        : 'Device unreachable. No data received yet.'}
    </Alert>
  );
}
