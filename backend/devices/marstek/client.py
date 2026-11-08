"""The only module that talks to the Marstek device (JSON-RPC over UDP).

Angular analogy: an injectable service that wraps HttpClient. Everything else (views, the stats
poller, AI tools) gets it from `get_client()`, so tests can swap in a fake.
"""

import itertools
import json
import logging
import re
import socket
import threading
import time
from collections.abc import Callable
from functools import lru_cache
from typing import Any, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from devices.marstek.exceptions import DeviceRpcError, DeviceTimeout
from devices.marstek.types import (
    BatteryStatus,
    BleStatus,
    DeviceInfo,
    EmStatus,
    EsStatus,
    ModeConfig,
    ModeStatus,
    PowerVersion,
    PvStatus,
    ResetType,
    SetResult,
    WifiStatus,
)

logger = logging.getLogger(__name__)

SocketFactory = Callable[[], socket.socket]
MAX_DATAGRAM = 65535
DOD_MIN, DOD_MAX = 30, 88
POWER_VERSIONS: frozenset[int] = frozenset({800, 1200, 1500, 2200, 2500})
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _udp_socket() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


class MarstekClient:
    """Sends one JSON-RPC request per UDP datagram and waits for the matching reply.

    - Replies are matched by `id`; stray or malformed packets are ignored.
    - Reads are retried on timeout. Writes are **never** retried: a lost reply doesn't mean the
      command wasn't applied, and resending e.g. a factory reset is not something to do blindly.
    - A lock serializes calls, because the device is a small single UDP endpoint.
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 2.0,
        retries: int = 2,
        socket_factory: SocketFactory | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self._socket_factory = socket_factory
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    # --- transport -----------------------------------------------------------------------------

    def _open(self) -> socket.socket:
        # Looked up at call time (not as a default arg) so the test safety net can patch it.
        return (self._socket_factory or _udp_socket)()

    def call(self, method: str, params: dict[str, Any], *, write: bool = False) -> dict[str, Any]:
        """Send `method` and return its `result`. Raises DeviceTimeout / DeviceRpcError."""
        attempts = 1 if write else 1 + self.retries
        if write:
            logger.info("write %s %s -> %s:%s", method, params, self.host, self.port)
        with self._lock:
            for attempt in range(1, attempts + 1):
                req_id = next(self._ids)
                try:
                    return self._send_and_wait(req_id, method, params)
                except DeviceTimeout:
                    logger.warning("%s timed out (attempt %d/%d)", method, attempt, attempts)
        raise DeviceTimeout(method)

    def _send_and_wait(self, req_id: int, method: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps({"id": req_id, "method": method, "params": params}).encode()
        deadline = time.monotonic() + self.timeout
        with self._open() as sock:
            sock.sendto(payload, (self.host, self.port))
            while (remaining := deadline - time.monotonic()) > 0:
                sock.settimeout(remaining)
                try:
                    data, _addr = sock.recvfrom(MAX_DATAGRAM)
                except TimeoutError:
                    break
                msg = _parse(data)
                if msg is None or msg.get("id") != req_id:
                    continue  # stray packet (e.g. a late reply to an earlier retry)
                if "error" in msg:
                    err = msg["error"]
                    raise DeviceRpcError(
                        int(err.get("code", 0)), str(err.get("message", "")), err.get("data")
                    )
                return cast(dict[str, Any], msg.get("result", {}))
        raise DeviceTimeout(method)

    def discover(self, timeout: float | None = None) -> list[DeviceInfo]:
        """Broadcast Marstek.GetDevice and collect every reply until `timeout` (deduped by MAC)."""
        wait = self.timeout if timeout is None else timeout
        req_id = next(self._ids)
        payload = json.dumps(
            {"id": req_id, "method": "Marstek.GetDevice", "params": {"ble_mac": "0"}}
        ).encode()
        found: dict[str, DeviceInfo] = {}
        deadline = time.monotonic() + wait
        with self._lock, self._open() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(payload, ("255.255.255.255", self.port))
            while (remaining := deadline - time.monotonic()) > 0:
                sock.settimeout(remaining)
                try:
                    data, _addr = sock.recvfrom(MAX_DATAGRAM)
                except TimeoutError:
                    break
                msg = _parse(data)
                if msg is None or msg.get("id") != req_id or "result" not in msg:
                    continue
                info = cast(DeviceInfo, msg["result"])
                found[info.get("ble_mac") or info.get("ip", "")] = info
        return list(found.values())

    # --- reads ---------------------------------------------------------------------------------

    def get_device(self, ble_mac: str = "0") -> DeviceInfo:
        return cast(DeviceInfo, self.call("Marstek.GetDevice", {"ble_mac": ble_mac}))

    def get_wifi_status(self, instance: int = 0) -> WifiStatus:
        return cast(WifiStatus, self.call("Wifi.GetStatus", {"id": instance}))

    def get_ble_status(self, instance: int = 0) -> BleStatus:
        return cast(BleStatus, self.call("BLE.GetStatus", {"id": instance}))

    def get_battery_status(self, instance: int = 0) -> BatteryStatus:
        return cast(BatteryStatus, self.call("Bat.GetStatus", {"id": instance}))

    def get_pv_status(self, instance: int = 0) -> PvStatus:
        return cast(PvStatus, self.call("PV.GetStatus", {"id": instance}))

    def get_es_status(self, instance: int = 0) -> EsStatus:
        return cast(EsStatus, self.call("ES.GetStatus", {"id": instance}))

    def get_mode(self, instance: int = 0) -> ModeStatus:
        return cast(ModeStatus, self.call("ES.GetMode", {"id": instance}))

    def get_em_status(self, instance: int = 0) -> EmStatus:
        return cast(EmStatus, self.call("EM.GetStatus", {"id": instance}))

    # --- writes (change real hardware; serializers validate first, these re-check) -------------

    def set_mode(self, config: ModeConfig, instance: int = 0) -> SetResult:
        _check_mode_config(config)
        result = self.call("ES.SetMode", {"id": instance, "config": config}, write=True)
        return cast(SetResult, result)

    def set_dod(self, value: int, instance: int = 0) -> SetResult:
        if not DOD_MIN <= value <= DOD_MAX:
            raise ValueError(f"DOD must be {DOD_MIN}-{DOD_MAX}, got {value}")
        return cast(SetResult, self.call("DOD.SET", {"id": instance, "value": value}, write=True))

    def set_ble_advertising(self, enabled: bool, instance: int = 0) -> SetResult:
        # Inverted on the wire: 0 = enable, 1 = disable.
        params = {"id": instance, "enable": 0 if enabled else 1}
        return cast(SetResult, self.call("Ble.Adv", params, write=True))

    def set_led(self, on: bool, instance: int = 0) -> SetResult:
        params = {"id": instance, "state": 1 if on else 0}
        return cast(SetResult, self.call("Led.Ctrl", params, write=True))

    def set_power_version(self, version: PowerVersion, instance: int = 0) -> SetResult:
        if version not in POWER_VERSIONS:
            raise ValueError(f"version must be one of {sorted(POWER_VERSIONS)}, got {version}")
        params = {"id": instance, "version": version}
        return cast(SetResult, self.call("Set.Ver", params, write=True))

    def reset_factory(
        self, reset_type: ResetType, *, confirmed: bool, instance: int = 0
    ) -> SetResult:
        """⚠️ Factory reset. Callers must pass `confirmed=True` after explicit user confirmation."""
        if not confirmed:
            raise PermissionError("Reset.Factory requires explicit confirmation")
        if reset_type not in (1, 2):
            raise ValueError(f"reset type must be 1 or 2, got {reset_type}")
        params = {"id": instance, "type": reset_type}
        return cast(SetResult, self.call("Reset.Factory", params, write=True))


def _parse(data: bytes) -> dict[str, Any] | None:
    try:
        msg = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return msg if isinstance(msg, dict) else None


def _check_mode_config(config: ModeConfig) -> None:
    expected = {
        "Auto": "auto_cfg",
        "AI": "ai_cfg",
        "Manual": "manual_cfg",
        "Passive": "passive_cfg",
        "UPS": "ups_cfg",
    }
    key = expected.get(config["mode"])
    if key is None:
        raise ValueError(f"unknown mode {config['mode']!r}")
    extra = {k for k in config if k.endswith("_cfg")} - {key}
    if key not in config or extra:
        raise ValueError(f"mode {config['mode']} needs exactly `{key}`")
    manual = config.get("manual_cfg")
    if manual is not None:
        for field in ("start_time", "end_time"):
            if not _HHMM.match(manual[field]):
                raise ValueError(f"{field} must be hh:mm, got {manual[field]!r}")
        if not 0 <= manual["week_set"] <= 0x7F:
            raise ValueError("week_set must fit in 7 bits")


@lru_cache(maxsize=32)
def client_for(host: str, port: int) -> MarstekClient:
    """One shared client (and so one lock) per device address. Tests replace this."""
    return MarstekClient(host, port, settings.MARSTEK_TIMEOUT)


def get_client() -> MarstekClient:
    """Client for the device in `.env`."""
    if not settings.MARSTEK_HOST:
        raise ImproperlyConfigured("MARSTEK_HOST is not set (see .env.example)")
    return client_for(settings.MARSTEK_HOST, settings.MARSTEK_PORT)


def get_discovery_client() -> MarstekClient:
    """Client used only for broadcast discovery (no target host needed)."""
    return client_for("255.255.255.255", settings.MARSTEK_PORT)
