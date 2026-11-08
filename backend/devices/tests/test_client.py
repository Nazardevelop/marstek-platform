"""MarstekClient tests. Every socket is a FakeSocket; responses come from the spec's examples."""

import json
import socket
from typing import Any

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from devices.marstek.client import MarstekClient, get_client
from devices.marstek.exceptions import DeviceRpcError, DeviceTimeout
from devices.marstek.types import ModeConfig
from devices.tests.fakes import FakeNetwork, error, load_doc_examples, reply

EXAMPLES = load_doc_examples()


def doc_result(method: str, variant: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = EXAMPLES[(method, "response", variant)]["result"]
    return result


def echo_doc(method: str) -> FakeNetwork:
    return FakeNetwork(lambda req: [reply(req, doc_result(method))])


# --- spec examples ------------------------------------------------------------------------------


def test_doc_examples_parse() -> None:
    methods = {m for (m, kind, _) in EXAMPLES if kind == "response"}
    assert {"Bat.GetStatus", "ES.GetStatus", "ES.GetMode", "EM.GetStatus"} <= methods


@pytest.mark.parametrize(
    ("method", "call"),
    [
        ("Wifi.GetStatus", lambda c: c.get_wifi_status()),
        ("BLE.GetStatus", lambda c: c.get_ble_status()),
        ("Bat.GetStatus", lambda c: c.get_battery_status()),
        ("PV.GetStatus", lambda c: c.get_pv_status()),
        ("ES.GetStatus", lambda c: c.get_es_status()),
        ("ES.GetMode", lambda c: c.get_mode()),
        ("EM.GetStatus", lambda c: c.get_em_status()),
    ],
)
def test_read_methods_send_spec_request_and_return_result(method: str, call: Any) -> None:
    net = echo_doc(method)
    assert call(net.client()) == doc_result(method)
    (request,) = net.requests
    assert request["method"] == method
    assert request["params"] == {"id": 0}
    assert net.sockets[0].sent[0][1] == ("192.168.1.50", 30000)


def test_get_device_targets_ble_mac() -> None:
    result = EXAMPLES[("Marstek.GetDevice", "response", None)]["result"]
    net = FakeNetwork(lambda req: [reply(req, result)])
    assert net.client().get_device("abc123")["device"] == result["device"]
    assert net.requests[0]["params"] == {"ble_mac": "abc123"}


# --- transport ----------------------------------------------------------------------------------


def test_ignores_stray_and_malformed_packets() -> None:
    def responder(req: dict[str, Any]) -> list[bytes]:
        stale = json.dumps({"id": req["id"] - 1, "result": {"soc": 1}}).encode()
        return [b"\xff not json", stale, reply(req, {"soc": 99})]

    assert FakeNetwork(responder).client().get_battery_status()["soc"] == 99


def test_rpc_error_raises_with_code() -> None:
    net = FakeNetwork(lambda req: [error(req, -32601, "Method not found")])
    with pytest.raises(DeviceRpcError) as exc:
        net.client().get_pv_status()
    assert exc.value.code == -32601
    assert exc.value.message == "Method not found"


def test_read_retries_then_succeeds() -> None:
    calls = 0

    def responder(req: dict[str, Any]) -> list[bytes]:
        nonlocal calls
        calls += 1
        return [] if calls < 3 else [reply(req, {"soc": 50})]

    net = FakeNetwork(responder)
    assert net.client(retries=2).get_battery_status()["soc"] == 50
    ids = [r["id"] for r in net.requests]
    assert len(ids) == 3
    assert len(set(ids)) == 3  # each retry gets a fresh id


def test_read_times_out_after_retries() -> None:
    net = FakeNetwork(lambda req: [])
    with pytest.raises(DeviceTimeout):
        net.client(retries=2).get_es_status()
    assert len(net.requests) == 3


def test_writes_are_never_retried() -> None:
    net = FakeNetwork(lambda req: [])
    with pytest.raises(DeviceTimeout):
        net.client(retries=5).set_led(True)
    assert len(net.requests) == 1


def test_discover_broadcasts_and_dedupes() -> None:
    a = {"device": "VenusC", "ver": 150, "ble_mac": "aa", "wifi_mac": "1", "wifi_name": "x",
         "ip": "192.168.1.50"}  # fmt: skip
    b = {**a, "ble_mac": "bb", "ip": "192.168.1.51"}
    net = FakeNetwork(lambda req: [reply(req, a), reply(req, a), reply(req, b)])
    found = net.client().discover(timeout=0.2)
    assert sorted(d["ble_mac"] for d in found) == ["aa", "bb"]
    sock = net.sockets[0]
    assert sock.sent[0][1] == ("255.255.255.255", 30000)
    assert sock.sent[0][0]["params"] == {"ble_mac": "0"}
    assert (socket.SOL_SOCKET, socket.SO_BROADCAST, 1) in sock.options


# --- writes: wire format + validation (fake socket only) ----------------------------------------


def ok() -> FakeNetwork:
    return FakeNetwork(lambda req: [reply(req, {"id": 0, "set_result": True})])


@pytest.mark.parametrize("variant", ["Auto", "AI", "Manual", "Passive", "UPS"])
def test_set_mode_sends_spec_config(variant: str) -> None:
    spec_request = EXAMPLES[("ES.SetMode", "request", variant)]
    net = ok()
    assert net.client().set_mode(spec_request["params"]["config"])["set_result"] is True
    assert net.requests[0]["method"] == "ES.SetMode"
    assert net.requests[0]["params"] == spec_request["params"]


@pytest.mark.parametrize(
    "config",
    [
        {"mode": "Turbo", "auto_cfg": {"enable": 1}},
        {"mode": "Auto"},
        {"mode": "Auto", "auto_cfg": {"enable": 1}, "ai_cfg": {"enable": 1}},
        {"mode": "Manual", "manual_cfg": {"time_num": 0, "start_time": "25:00", "end_time": "20:30",
                                          "week_set": 127, "power": 100, "enable": 1}},
        {"mode": "Manual", "manual_cfg": {"time_num": 0, "start_time": "08:00", "end_time": "20:30",
                                          "week_set": 128, "power": 100, "enable": 1}},
    ],
)  # fmt: skip
def test_set_mode_rejects_bad_config_without_sending(config: ModeConfig) -> None:
    net = ok()
    with pytest.raises(ValueError):
        net.client().set_mode(config)
    assert net.requests == []


def test_set_dod_range() -> None:
    net = ok()
    net.client().set_dod(30)
    net.client().set_dod(88)
    for bad in (29, 89):
        with pytest.raises(ValueError):
            net.client().set_dod(bad)
    assert [r["params"]["value"] for r in net.requests] == [30, 88]


def test_ble_advertising_is_inverted_on_the_wire() -> None:
    net = ok()
    net.client().set_ble_advertising(True)
    net.client().set_ble_advertising(False)
    assert [r["params"]["enable"] for r in net.requests] == [0, 1]


def test_led() -> None:
    net = ok()
    net.client().set_led(True)
    net.client().set_led(False)
    assert [r["params"]["state"] for r in net.requests] == [1, 0]


def test_power_version_choices() -> None:
    net = ok()
    net.client().set_power_version(2500)
    with pytest.raises(ValueError):
        net.client().set_power_version(1000)  # type: ignore[arg-type]
    assert [r["params"]["version"] for r in net.requests] == [2500]


def test_factory_reset_requires_confirmation() -> None:
    net = ok()
    with pytest.raises(PermissionError):
        net.client().reset_factory(1, confirmed=False)
    with pytest.raises(ValueError):
        net.client().reset_factory(3, confirmed=True)  # type: ignore[arg-type]
    assert net.requests == []  # nothing ever left the (fake) socket


# --- factory + safety net -----------------------------------------------------------------------


@override_settings(MARSTEK_HOST="")
def test_get_client_requires_host() -> None:
    with pytest.raises(ImproperlyConfigured):
        get_client()


@override_settings(MARSTEK_HOST="192.168.1.50", MARSTEK_PORT=30001, MARSTEK_TIMEOUT=1.5)
def test_get_client_reads_settings_and_is_cached() -> None:
    client = get_client()
    assert (client.host, client.port, client.timeout) == ("192.168.1.50", 30001, 1.5)
    assert get_client() is client


def test_real_sockets_are_blocked_in_tests() -> None:
    with pytest.raises(RuntimeError, match="must not open real UDP sockets"):
        MarstekClient("192.168.1.50", 30000).get_battery_status()
