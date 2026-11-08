import { CardGrid } from '@/components/CardGrid';
import { PageTitle } from '@/components/PageTitle';
import { QueryState } from '@/components/QueryState';
import { RequireDevice } from '@/features/device/components/RequireDevice';
import { useStatus } from '@/features/device/hooks';
import { BatteryCard } from './components/BatteryCard';
import { CtCard } from './components/CtCard';
import { ModeCard } from './components/ModeCard';
import { PowerFlowCard } from './components/PowerFlowCard';
import { PvCard } from './components/PvCard';
import { TodayEnergyCard } from './components/TodayEnergyCard';

function Dashboard({ deviceId, hasPv }: { deviceId: number; hasPv: boolean }) {
  const { data, isPending, error } = useStatus(deviceId);
  if (!data) return <QueryState isPending={isPending} error={error} label="live status" />;
  return (
    <CardGrid>
      <BatteryCard battery={data.battery} systemSocPct={data.system_soc_pct} />
      <PowerFlowCard power={data.power} />
      <ModeCard mode={data.mode} />
      <TodayEnergyCard deviceId={deviceId} />
      <CtCard ct={data.ct} />
      {hasPv && data.pv && <PvCard inputs={data.pv} />}
    </CardGrid>
  );
}

export function DashboardPage() {
  return (
    <>
      <PageTitle>Dashboard</PageTitle>
      <RequireDevice>
        {(device) => <Dashboard deviceId={device.id} hasPv={device.capabilities.pv} />}
      </RequireDevice>
    </>
  );
}
