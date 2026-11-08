import Alert from '@mui/material/Alert';
import type { Device } from '@/api/types';
import { StatCard } from '@/components/StatCard';
import { BleSetting, LedSetting } from './ToggleSettings';
import { DodSetting } from './DodSetting';
import { PowerVersionSetting } from './PowerVersionSetting';

export function SystemSettingsCard({ device }: { device: Device }) {
  return (
    <StatCard title="System settings">
      <Alert severity="info" variant="outlined" sx={{ mb: 1 }}>
        The device can't report these values back, so the controls don't show the current state.
      </Alert>
      <DodSetting deviceId={device.id} />
      <LedSetting deviceId={device.id} />
      <BleSetting deviceId={device.id} />
      {device.capabilities.power_version && <PowerVersionSetting deviceId={device.id} />}
    </StatCard>
  );
}
