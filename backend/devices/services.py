"""Device use cases: turn raw device payloads into clean API data (W, Wh, booleans, lists).

Views call these; they call the client. (Angular: component → service → HttpClient.)
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from devices.capabilities import Capabilities, capabilities_for
from devices.marstek.client import MarstekClient, client_for, get_discovery_client
from devices.marstek.exceptions import DeviceRpcError, DeviceTimeout
from devices.marstek.types import (
    BatteryStatus,
    BleStatus,
    DeviceInfo,
    EmStatus,
    EsStatus,
    ModeStatus,
    PvStatus,
    WifiStatus,
)
from devices.models import Device

logger = logging.getLogger(__name__)
PV_INPUTS = range(1, 5)


def client(device: Device) -> MarstekClient:
    return client_for(device.host, device.port)


# --- unit helpers -------------------------------------------------------------------------------


def num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scale(value: Any, factor: float) -> float | None:
    n = num(value)
    return None if n is None else round(n * factor, 3)


def _bool(value: Any) -> bool | None:
    return None if value is None else bool(value)


# --- normalizers (pure, unit-tested against the spec examples) ----------------------------------


def normalize_battery(raw: BatteryStatus) -> dict[str, Any]:
    return {
        "soc_pct": num(raw.get("soc")),  # PDF says string, example is a number
        "charge_allowed": _bool(raw.get("charg_flag")),
        "discharge_allowed": _bool(raw.get("dischrg_flag")),
        "temperature_c": num(raw.get("bat_temp")),
        "remaining_wh": num(raw.get("bat_capacity")),
        "rated_wh": num(raw.get("rated_capacity")),
    }


def normalize_es(raw: EsStatus) -> dict[str, Any]:
    return {
        "power": {
            "pv_w": num(raw.get("pv_power")),
            "grid_w": num(raw.get("ongrid_power")),
            "offgrid_w": num(raw.get("offgrid_power")),
            "battery_w": num(raw.get("bat_power")),
        },
        "energy": {
            "pv_total_wh": _scale(raw.get("total_pv_energy"), 10),  # 0.01 kWh → Wh
            "grid_import_wh": num(raw.get("total_grid_input_energy")),
            "grid_export_wh": num(raw.get("total_grid_output_energy")),
            "load_total_wh": num(raw.get("total_load_energy")),
        },
        "system_soc_pct": num(raw.get("bat_soc")),
        "system_capacity_wh": num(raw.get("bat_cap")),
    }


def normalize_em(raw: EmStatus) -> dict[str, Any]:
    return {
        "connected": raw.get("ct_state") == 1,
        "phase_a_w": num(raw.get("a_power")),
        "phase_b_w": num(raw.get("b_power")),
        "phase_c_w": num(raw.get("c_power")),
        "total_w": num(raw.get("total_power")),
        "import_wh": _scale(raw.get("input_energy"), 0.1),  # 0.1 Wh → Wh
        "export_wh": _scale(raw.get("output_energy"), 0.1),
    }


def normalize_mode(raw: ModeStatus) -> dict[str, Any]:
    return {"mode": str(raw.get("mode", "")).lower() or None}


def normalize_pv(raw: PvStatus) -> list[dict[str, Any]]:
    return [
        {
            "input": n,
            "power_w": num(raw.get(f"pv{n}_power")),
            "voltage_v": num(raw.get(f"pv{n}_voltage")),
            "current_a": num(raw.get(f"pv{n}_current")),
            "active": raw.get(f"pv{n}_state") == 1,
        }
        for n in PV_INPUTS
        if f"pv{n}_power" in raw
    ]


def normalize_wifi(raw: WifiStatus) -> dict[str, Any]:
    return {
        "ssid": raw.get("ssid"),
        "rssi_dbm": num(raw.get("rssi")),
        "ip": raw.get("sta_ip"),
        "gateway": raw.get("sta_gate"),
        "netmask": raw.get("sta_mask"),
        "dns": raw.get("sta_dns"),
        "mac": raw.get("wifi_mac"),
    }


def normalize_ble(raw: BleStatus) -> dict[str, Any]:
    return {"state": raw.get("state"), "mac": raw.get("ble_mac")}


# --- device registry ----------------------------------------------------------------------------


def ensure_default_device() -> None:
    """Create the `.env` device on first use, so a fresh install works without discovery."""
    if settings.MARSTEK_HOST and not Device.objects.exists():
        Device.objects.create(host=settings.MARSTEK_HOST, port=settings.MARSTEK_PORT)


def capabilities(device: Device) -> Capabilities:
    return capabilities_for(device.model, device.firmware)


def _apply_info(device: Device, info: DeviceInfo) -> None:
    device.model = info.get("device", device.model)
    device.firmware = info.get("ver", device.firmware)
    device.ble_mac = info.get("ble_mac", device.ble_mac)
    device.wifi_mac = info.get("wifi_mac", device.wifi_mac)
    device.last_seen = timezone.now()


def refresh_info(device: Device) -> Device:
    """Re-read model/firmware/MACs. On timeout, keep what we have (the device shows offline)."""
    try:
        info = client(device).get_device()
    except DeviceTimeout:
        return device
    _apply_info(device, info)
    device.save()
    return device


@transaction.atomic
def discover() -> list[Device]:
    """Broadcast on the LAN and upsert every device that answers (matched by BLE MAC)."""
    devices = []
    for info in get_discovery_client().discover():
        mac = info.get("ble_mac", "")
        device = Device.objects.filter(ble_mac=mac).first() if mac else None
        if device is None:
            device = Device(name=info.get("device") or "Marstek")
        device.host = info.get("ip", device.host)
        device.port = settings.MARSTEK_PORT
        _apply_info(device, info)
        device.save()
        devices.append(device)
    return devices


# --- live reads with last-known fallback --------------------------------------------------------


def read_or_cached(device: Device, key: str, read: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Read live; on timeout return the cached copy marked stale, or re-raise if there is none."""
    try:
        data = read()
    except DeviceTimeout:
        cached = device.cached(key)
        if cached is None:
            raise
        logger.info("device %s unreachable, serving cached %s", device.pk, key)
        return {**cached, "stale": True}
    now: datetime = timezone.now()
    payload = {**data, "fetched_at": now.isoformat()}
    device.cache = {**device.cache, key: payload}
    device.last_seen = now
    device.save(update_fields=["cache", "last_seen"])
    return {**payload, "stale": False}


def _optional[T](read: Callable[[], T]) -> T | None:
    """A read the model may reject (e.g. PV on Venus C): treat 'method not found' as absent."""
    try:
        return read()
    except DeviceRpcError as exc:
        logger.info("optional read failed: %s", exc)
        return None


def get_status(device: Device) -> dict[str, Any]:
    """Dashboard aggregate: battery, power, energy, CT meter, mode and (Venus A/D) PV inputs."""

    def read() -> dict[str, Any]:
        c = client(device)
        es = normalize_es(c.get_es_status())
        pv = _optional(c.get_pv_status) if capabilities(device).pv else None
        return {
            "battery": normalize_battery(c.get_battery_status()),
            **es,
            "ct": normalize_em(c.get_em_status()),
            **normalize_mode(c.get_mode()),
            "pv": normalize_pv(pv) if pv is not None else None,
        }

    return read_or_cached(device, "status", read)


def get_network(device: Device) -> dict[str, Any]:
    def read() -> dict[str, Any]:
        c = client(device)
        return {
            "wifi": normalize_wifi(c.get_wifi_status()),
            "bluetooth": normalize_ble(c.get_ble_status()),
        }

    return read_or_cached(device, "network", read)
