"""Raw device payloads, exactly as `docs/MarstekDeviceOpenApi.md` describes them.

These are the device's shapes (like a TS interface for a backend response). Unit conversion and
quirk-hiding happen later in `devices.services`, never here.
"""

from typing import Literal, NotRequired, TypedDict

# --- reads -------------------------------------------------------------------------------------


class DeviceInfo(TypedDict):
    """Marstek.GetDevice"""

    device: str  # model, e.g. "VenusC"
    ver: int  # firmware version
    ble_mac: str
    wifi_mac: str
    wifi_name: str
    ip: str


class WifiStatus(TypedDict):
    id: int
    wifi_mac: str
    ssid: str | None
    rssi: int
    sta_ip: str | None
    sta_gate: str | None
    sta_mask: str | None
    sta_dns: str | None


class BleStatus(TypedDict):
    id: NotRequired[int]
    state: str
    ble_mac: str


class BatteryStatus(TypedDict):
    id: int
    soc: int | str  # PDF says string, example is a number
    charg_flag: bool
    dischrg_flag: bool
    bat_temp: float | None
    bat_capacity: float | None  # Wh
    rated_capacity: float | None  # Wh


# PV.GetStatus returns pv1_power … pv4_state (dynamic keys), so it's a plain mapping.
PvStatus = dict[str, float]


class EsStatus(TypedDict):
    id: int | None
    bat_soc: int | None
    bat_cap: float | None  # Wh
    pv_power: float | None  # W
    ongrid_power: float | None  # W
    offgrid_power: float | None  # W
    bat_power: NotRequired[float | None]  # W, in the table but missing from the example
    total_pv_energy: float | None  # 0.01 kWh (!)
    total_grid_output_energy: float | None  # Wh
    total_grid_input_energy: float | None  # Wh
    total_load_energy: float | None  # Wh


class EmStatus(TypedDict):
    id: int | None
    ct_state: int | None  # 0 = not connected, 1 = connected
    a_power: float | None
    b_power: float | None
    c_power: float | None
    total_power: float | None
    input_energy: float | None  # 0.1 Wh (!)
    output_energy: float | None  # 0.1 Wh (!)


class ModeStatus(TypedDict):
    """ES.GetMode. CT fields are only valid in Auto/AI mode."""

    id: int | None
    mode: str
    ongrid_power: float | None
    offgrid_power: float | None
    bat_soc: int | None
    ct_state: NotRequired[int | None]
    a_power: NotRequired[float | None]
    b_power: NotRequired[float | None]
    c_power: NotRequired[float | None]
    total_power: NotRequired[float | None]
    input_energy: NotRequired[float | None]  # 0.1 Wh
    output_energy: NotRequired[float | None]  # 0.1 Wh


# --- writes ------------------------------------------------------------------------------------


class SetResult(TypedDict):
    id: NotRequired[int]
    set_result: bool


ModeName = Literal["Auto", "AI", "Manual", "Passive", "UPS"]


class EnableCfg(TypedDict):
    enable: Literal[0, 1]


class ManualCfg(TypedDict):
    time_num: int  # slot index: 0-9 (E mini: 0-5)
    start_time: str  # "hh:mm"
    end_time: str  # "hh:mm"
    week_set: int  # bit0 = Monday … bit6 = Sunday
    power: int  # W
    enable: Literal[0, 1]
    manual_set: NotRequired[Literal[0, 1, 2, 3]]  # E mini only


class PassiveCfg(TypedDict):
    power: int  # W
    cd_time: int  # countdown, s


class ModeConfig(TypedDict):
    """`config` for ES.SetMode. Send only the *_cfg that matches `mode`."""

    mode: ModeName
    auto_cfg: NotRequired[EnableCfg]
    ai_cfg: NotRequired[EnableCfg]
    manual_cfg: NotRequired[ManualCfg]
    passive_cfg: NotRequired[PassiveCfg]
    ups_cfg: NotRequired[EnableCfg]


PowerVersion = Literal[800, 1200, 1500, 2200, 2500]
ResetType = Literal[1, 2]
