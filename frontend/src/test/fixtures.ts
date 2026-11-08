import type { DailyEnergy, Device, History, ModeStatus, Network, Status } from '@/api/types';

export const API = 'http://api.test/api/v1';

export const device: Device = {
  id: 1,
  name: 'Venus',
  host: '192.168.1.11',
  port: 30000,
  model: 'VenusD',
  firmware: 155,
  ble_mac: '123456789012',
  wifi_mac: '012123456789',
  last_seen: '2026-11-08T10:00:00Z',
  online: true,
  capabilities: {
    pv: true,
    system_settings: true,
    power_version: true,
    factory_reset: true,
    manual_slots: 10,
    manual_action: false,
  },
};

export const status: Status = {
  fetched_at: '2026-11-08T10:00:00Z',
  stale: false,
  battery: {
    soc_pct: 82,
    charge_allowed: true,
    discharge_allowed: true,
    temperature_c: 25,
    remaining_wh: 4200,
    rated_wh: 5120,
  },
  power: { pv_w: 640, grid_w: -120, offgrid_w: 0, battery_w: -500 },
  energy: { pv_total_wh: 1000, grid_import_wh: 3273, grid_export_wh: 2548, load_total_wh: 0 },
  system_soc_pct: 82,
  system_capacity_wh: 5120,
  ct: {
    connected: false,
    phase_a_w: null,
    phase_b_w: null,
    phase_c_w: null,
    total_w: null,
    import_wh: null,
    export_wh: null,
  },
  mode: 'auto',
  pv: [
    { input: 1, power_w: 320, voltage_v: 38.2, current_a: 8.4, active: true },
    { input: 2, power_w: 320, voltage_v: 38.0, current_a: 8.4, active: true },
  ],
};

export const modeStatus: ModeStatus = {
  mode: 'auto',
  grid_w: -120,
  offgrid_w: 0,
  soc_pct: 82,
  ct: null,
  fetched_at: '2026-11-08T10:00:00Z',
  stale: false,
};

export const network: Network = {
  fetched_at: '2026-11-08T10:00:00Z',
  stale: false,
  wifi: {
    ssid: 'Home',
    rssi_dbm: -59,
    ip: '192.168.1.11',
    gateway: '192.168.1.1',
    netmask: '255.255.255.0',
    dns: '192.168.1.1',
    mac: '012123456789',
  },
  bluetooth: { state: 'connect', mac: '123456789012' },
};

export const daily: DailyEnergy[] = [
  { date: '2026-11-08', pv_wh: 2100, grid_import_wh: 300, grid_export_wh: 900, load_wh: 1500 },
];

export const history: History = { range: '24h', bucket_s: 300, metrics: [], points: [] };
