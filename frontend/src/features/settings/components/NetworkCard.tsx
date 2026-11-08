import { QueryState } from '@/components/QueryState';
import { StatCard } from '@/components/StatCard';
import { useNetwork } from '@/features/device/hooks';
import { InfoList } from './InfoList';

function signal(rssi: number | null): string {
  if (rssi == null) return '—';
  const quality = rssi >= -55 ? 'Excellent' : rssi >= -67 ? 'Good' : rssi >= -75 ? 'Fair' : 'Weak';
  return `${quality} (${rssi} dBm)`;
}

export function NetworkCard({ deviceId }: { deviceId: number }) {
  const { data, isPending, error } = useNetwork(deviceId);
  return (
    <StatCard title={data?.stale ? 'Network (last known)' : 'Network'}>
      {!data ? (
        <QueryState isPending={isPending} error={error} label="network info" />
      ) : (
        <InfoList
          rows={[
            ['WiFi', data.wifi.ssid],
            ['Signal', signal(data.wifi.rssi_dbm)],
            ['IP', data.wifi.ip],
            ['Gateway', data.wifi.gateway],
            ['Netmask', data.wifi.netmask],
            ['DNS', data.wifi.dns],
            ['Bluetooth', data.bluetooth.state],
          ]}
        />
      )}
    </StatCard>
  );
}
