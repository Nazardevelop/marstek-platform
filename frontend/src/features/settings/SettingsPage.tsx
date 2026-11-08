import Box from '@mui/material/Box';
import { PageTitle } from '@/components/PageTitle';
import { RequireDevice } from '@/features/device/components/RequireDevice';
import { ConnectionCard } from './components/ConnectionCard';
import { DangerZoneCard } from './components/DangerZoneCard';
import { DeviceInfoCard } from './components/DeviceInfoCard';
import { DiscoverCard } from './components/DiscoverCard';
import { NetworkCard } from './components/NetworkCard';
import { SystemSettingsCard } from './components/SystemSettingsCard';

export function SettingsPage() {
  return (
    <>
      <PageTitle>Device & settings</PageTitle>
      <Box sx={{ display: 'grid', gap: 2, maxWidth: 860 }}>
        <RequireDevice>
          {(device) => (
            <>
              <DeviceInfoCard device={device} />
              <NetworkCard deviceId={device.id} />
              <ConnectionCard device={device} />
              {device.capabilities.system_settings && <SystemSettingsCard device={device} />}
              {device.capabilities.factory_reset && <DangerZoneCard device={device} />}
            </>
          )}
        </RequireDevice>
        <DiscoverCard />
      </Box>
    </>
  );
}
