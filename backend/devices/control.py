"""Hardware writes: mode, system settings, factory reset. ⚠️ Everything here changes the device.

Every write: capability gate → per-device rate limit → audit log → device call.
Input is already validated by `devices.control_serializers`; the client re-checks ranges.
"""

import logging
from typing import Any, cast

from django.core.cache import cache
from rest_framework.exceptions import Throttled

from devices import services
from devices.control_serializers import MANUAL_ACTIONS, WEEKDAYS
from devices.marstek.exceptions import DeviceTimeout, UnsupportedFeature
from devices.marstek.types import (
    EmStatus,
    ManualCfg,
    ModeConfig,
    ModeStatus,
    PassiveCfg,
    PowerVersion,
    ResetType,
)
from devices.models import Device

logger = logging.getLogger("devices.audit")
WRITE_INTERVAL_S = 2


# --- week_set codec (bit0 = Monday … bit6 = Sunday) ---------------------------------------------


def weekdays_to_mask(days: list[str]) -> int:
    return sum(1 << WEEKDAYS.index(d) for d in set(days))


def mask_to_weekdays(mask: int) -> list[str]:
    return [d for i, d in enumerate(WEEKDAYS) if mask & (1 << i)]


# --- guards -------------------------------------------------------------------------------------


def _require(device: Device, feature: str, supported: bool) -> None:
    if not supported:
        raise UnsupportedFeature(f"{feature} is not supported by {device.model or 'this device'}")


def _rate_limit(device: Device) -> None:
    """At most one write per device every WRITE_INTERVAL_S (cache.add is atomic)."""
    if not cache.add(f"device-write:{device.pk}", 1, timeout=WRITE_INTERVAL_S):
        raise Throttled(wait=WRITE_INTERVAL_S, detail="Wait a moment between device commands")


def _audit(device: Device, action: str, detail: Any) -> None:
    logger.info("device=%s action=%s detail=%s", device.pk, action, detail)


# --- mode ---------------------------------------------------------------------------------------


def normalize_mode_status(raw: ModeStatus) -> dict[str, Any]:
    mode = str(raw.get("mode", "")).lower() or None
    ct = (
        services.normalize_em(cast(EmStatus, raw)) if mode in ("auto", "ai") else None
    )  # CT valid in Auto/AI only
    return {
        "mode": mode,
        "grid_w": services.num(raw.get("ongrid_power")),
        "offgrid_w": services.num(raw.get("offgrid_power")),
        "soc_pct": services.num(raw.get("bat_soc")),
        "ct": ct,
    }


def get_mode(device: Device) -> dict[str, Any]:
    return services.read_or_cached(
        device, "mode", lambda: normalize_mode_status(services.client(device).get_mode())
    )


def build_mode_configs(data: dict[str, Any]) -> list[ModeConfig]:
    """API body → ES.SetMode configs. Manual mode is one SetMode call per slot."""
    match data["mode"]:
        case "auto":
            return [{"mode": "Auto", "auto_cfg": {"enable": 1}}]
        case "ai":
            return [{"mode": "AI", "ai_cfg": {"enable": 1}}]
        case "ups":
            # Spec table says "Ups", its example says "UPS": verify on a real device.
            return [{"mode": "UPS", "ups_cfg": {"enable": 1}}]
        case "passive":
            cfg: PassiveCfg = {"power": data["power_w"], "cd_time": data["countdown_s"]}
            return [{"mode": "Passive", "passive_cfg": cfg}]
        case "manual":
            return [{"mode": "Manual", "manual_cfg": _manual_cfg(s)} for s in data["slots"]]
    raise ValueError(f"unknown mode {data['mode']!r}")


def _manual_cfg(slot: dict[str, Any]) -> ManualCfg:
    cfg: ManualCfg = {
        "time_num": slot["index"],
        "start_time": slot["start"],
        "end_time": slot["end"],
        "week_set": weekdays_to_mask(slot["weekdays"]),
        "power": slot["power_w"],
        "enable": 1 if slot["enabled"] else 0,
    }
    if "action" in slot:
        cfg["manual_set"] = MANUAL_ACTIONS.index(slot["action"])  # type: ignore[typeddict-item]
    return cfg


def set_mode(device: Device, data: dict[str, Any]) -> dict[str, Any]:
    _rate_limit(device)
    configs = build_mode_configs(data)
    _audit(device, "set_mode", data)
    c = services.client(device)
    slot_results: list[dict[str, Any]] = []
    ok = True
    for config in configs:
        ok = bool(c.set_mode(config).get("set_result"))
        if "manual_cfg" in config:
            slot_results.append({"index": config["manual_cfg"]["time_num"], "set_result": ok})
        if not ok:
            break  # don't keep programming slots after the device rejected one
    try:
        current: dict[str, Any] | None = normalize_mode_status(c.get_mode())
    except DeviceTimeout:
        current = None
    result: dict[str, Any] = {"set_result": ok, "current": current}
    if data["mode"] == "manual":
        result["slots"] = slot_results
    return result


# --- system settings ----------------------------------------------------------------------------


def _write(device: Device, action: str, detail: Any) -> None:
    _require(device, action, services.capabilities(device).system_settings)
    _rate_limit(device)
    _audit(device, action, detail)


def set_dod(device: Device, value: int) -> dict[str, Any]:
    _write(device, "dod", value)
    return {"set_result": bool(services.client(device).set_dod(value).get("set_result"))}


def set_led(device: Device, on: bool) -> dict[str, Any]:
    _write(device, "led", on)
    return {"set_result": bool(services.client(device).set_led(on).get("set_result"))}


def set_ble_advertising(device: Device, on: bool) -> dict[str, Any]:
    _write(device, "ble_advertising", on)
    result = services.client(device).set_ble_advertising(on)
    return {"set_result": bool(result.get("set_result"))}


def set_power_version(device: Device, watts: PowerVersion) -> dict[str, Any]:
    _require(device, "power version", services.capabilities(device).power_version)
    _rate_limit(device)
    _audit(device, "power_version", watts)
    result = services.client(device).set_power_version(watts)
    return {"set_result": bool(result.get("set_result"))}


def factory_reset(device: Device, reset_type: ResetType) -> dict[str, Any]:
    """⚠️ Only reachable through the confirmed API endpoint. Never an AI tool."""
    _require(device, "factory reset", services.capabilities(device).factory_reset)
    _rate_limit(device)
    logger.warning("device=%s action=FACTORY_RESET type=%s", device.pk, reset_type)
    result = services.client(device).reset_factory(reset_type, confirmed=True)
    return {"set_result": bool(result.get("set_result"))}
