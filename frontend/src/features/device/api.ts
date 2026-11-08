import { http, postJson } from '@/api/http';
import type {
  Device,
  ModeStatus,
  ModeWriteResult,
  Network,
  PatchDevice,
  SetModeRequest,
  SetResult,
  Status,
  PowerWatts,
  FactoryResetType,
} from '@/api/types';

const d = (id: number) => `/devices/${id}`;

export const listDevices = () => http<Device[]>('/devices/');
export const getDevice = (id: number) => http<Device>(`${d(id)}/`);
export const patchDevice = (id: number, body: PatchDevice) =>
  http<Device>(`${d(id)}/`, { method: 'PATCH', body: JSON.stringify(body) });
export const discoverDevices = () => postJson<Device[]>('/devices/discover/');

export const getStatus = (id: number) => http<Status>(`${d(id)}/status/`);
export const getMode = (id: number) => http<ModeStatus>(`${d(id)}/mode/`);
export const getNetwork = (id: number) => http<Network>(`${d(id)}/network/`);

// ⚠️ Write commands: these change real hardware.
export const setMode = (id: number, body: SetModeRequest) =>
  postJson<ModeWriteResult>(`${d(id)}/mode/`, body);
export const setDod = (id: number, value: number) =>
  postJson<SetResult>(`${d(id)}/settings/dod/`, { value });
export const setLed = (id: number, on: boolean) =>
  postJson<SetResult>(`${d(id)}/settings/led/`, { on });
export const setBleAdv = (id: number, on: boolean) =>
  postJson<SetResult>(`${d(id)}/settings/ble-adv/`, { on });
export const setPowerVersion = (id: number, watts: PowerWatts) =>
  postJson<SetResult>(`${d(id)}/settings/power-version/`, { watts });
export const factoryReset = (id: number, type: FactoryResetType, confirmName: string) =>
  postJson<SetResult>(`${d(id)}/factory-reset/`, { type, confirm_name: confirmName });
