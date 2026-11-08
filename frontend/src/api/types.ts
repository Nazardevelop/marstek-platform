// Friendly aliases over the generated OpenAPI types (src/api/schema.d.ts, `npm run gen:api`).
// Components import from here, never from schema.d.ts directly.
import type { components } from './schema';

type S = components['schemas'];

export type Device = S['Device'];
export type Capabilities = S['Capabilities'];
export type PatchDevice = Pick<S['PatchedDevice'], 'name' | 'host' | 'port'>;
export type Status = S['Status'];
export type PvInput = S['PvInput'];
export type ModeStatus = S['ModeStatus'];
export type Mode = S['ModeEnum'];
export type SetModeRequest = S['SetMode'];
export type ManualSlot = S['ManualSlot'];
export type Weekday = S['WeekdaysEnum'];
export type SlotAction = S['ActionEnum'];
export type ModeWriteResult = S['ModeWriteResult'];
export type SetResult = S['SetResult'];
export type Network = S['Network'];
export type History = S['History'];
export type HistoryPoint = S['HistoryPoint'];
export type HistoryRange = '24h' | '7d' | '30d';
export type DailyEnergy = S['DailyEnergy'];
export type PowerWatts = S['WattsEnum'];
export type FactoryResetType = S['TypeEnum'];
export type ChatMessage = S['ChatMessage'];
export type ChatContext = S['ChatContext'];
