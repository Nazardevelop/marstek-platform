import type { Device } from '@/api/types';
import { StatCard } from '@/components/StatCard';
import { formatTime } from '@/lib/format';
import { InfoList } from './InfoList';

export function DeviceInfoCard({ device }: { device: Device }) {
  return (
    <StatCard title="Device">
      <InfoList
        rows={[
          ['Name', device.name],
          ['Model', device.model],
          ['Firmware', device.firmware],
          ['BLE MAC', device.ble_mac],
          ['WiFi MAC', device.wifi_mac],
          ['Last seen', formatTime(device.last_seen)],
        ]}
      />
    </StatCard>
  );
}
