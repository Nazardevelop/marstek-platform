"""Write endpoints. The client is a MagicMock: we assert exactly what *would* go to the device."""

from typing import Any
from unittest.mock import MagicMock, call

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from devices import control
from devices.control_serializers import WEEKDAYS
from devices.marstek.client import MarstekClient
from devices.marstek.exceptions import DeviceTimeout
from devices.models import Device
from devices.tests.fakes import load_doc_examples

pytestmark = pytest.mark.django_db
EXAMPLES = load_doc_examples()
OK = {"id": 0, "set_result": True}
WRITES = ("set_mode", "set_dod", "set_led", "set_ble_advertising", "set_power_version",
          "reset_factory")  # fmt: skip


@pytest.fixture(autouse=True)
def _clear_rate_limit() -> None:
    cache.clear()


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    client = MagicMock(spec=MarstekClient)
    client.get_mode.return_value = EXAMPLES[("ES.GetMode", "response", None)]["result"]
    for write in WRITES:
        getattr(client, write).return_value = OK
    monkeypatch.setattr("devices.services.client_for", lambda host, port: client)
    return client


def make_device(model: str = "VenusC", firmware: int = 150, name: str = "Home") -> Device:
    return Device.objects.create(name=name, host="192.168.1.50", model=model, firmware=firmware)


def post(api: APIClient, name: str, device: Device, body: dict[str, Any]) -> Any:
    return api.post(reverse(name, args=[device.pk]), body, format="json")


def assert_no_writes(fake: MagicMock) -> None:
    for write in WRITES:
        getattr(fake, write).assert_not_called()


def slot(**overrides: Any) -> dict[str, Any]:
    base = {"index": 0, "start": "08:30", "end": "20:30", "weekdays": ["mon", "tue"],
            "power_w": 100, "enabled": True}  # fmt: skip
    return {**base, **overrides}


# --- week_set codec -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("days", "mask"),
    [([], 0), (["mon"], 1), (["mon", "tue"], 3), (["sun"], 64), (WEEKDAYS, 127)],
)
def test_week_set_round_trip(days: list[str], mask: int) -> None:
    assert control.weekdays_to_mask(days) == mask
    assert control.mask_to_weekdays(mask) == days


# --- mode ---------------------------------------------------------------------------------------


def test_get_mode_includes_ct_only_in_auto(api: APIClient, fake: MagicMock) -> None:
    device = make_device()
    body = api.get(reverse("device-mode", args=[device.pk])).json()
    assert body["mode"] == "auto"
    assert body["ct"]["import_wh"] == 308632.0  # 0.1 Wh → Wh
    cache.clear()
    fake.get_mode.return_value = {**fake.get_mode.return_value, "mode": "Manual"}
    assert api.get(reverse("device-mode", args=[device.pk])).json()["ct"] is None


@pytest.mark.parametrize(
    ("body", "variant"),
    [
        ({"mode": "auto"}, "Auto"),
        ({"mode": "ai"}, "AI"),
        ({"mode": "ups"}, "UPS"),
        ({"mode": "passive", "power_w": 100, "countdown_s": 300}, "Passive"),
    ],
)
def test_simple_modes_send_spec_config(
    api: APIClient, fake: MagicMock, body: dict[str, Any], variant: str
) -> None:
    res = post(api, "device-mode", make_device(), body)
    assert res.status_code == 200
    assert res.json()["set_result"] is True
    assert res.json()["current"]["mode"] == "auto"  # read back after the write
    expected = EXAMPLES[("ES.SetMode", "request", variant)]["params"]["config"]
    fake.set_mode.assert_called_once_with(expected)


def test_manual_mode_one_call_per_slot(api: APIClient, fake: MagicMock) -> None:
    body = {"mode": "manual", "slots": [
        slot(index=0, weekdays=WEEKDAYS),
        slot(index=3, start="22:00", end="06:00", weekdays=["sun", "sat"], power_w=-800,
             enabled=False),
    ]}  # fmt: skip
    res = post(api, "device-mode", make_device(), body)
    assert res.status_code == 200
    assert res.json()["slots"] == [
        {"index": 0, "set_result": True},
        {"index": 3, "set_result": True},
    ]
    fake.set_mode.assert_has_calls([
        call({"mode": "Manual", "manual_cfg": {"time_num": 0, "start_time": "08:30",
              "end_time": "20:30", "week_set": 127, "power": 100, "enable": 1}}),
        call({"mode": "Manual", "manual_cfg": {"time_num": 3, "start_time": "22:00",
              "end_time": "06:00", "week_set": 96, "power": -800, "enable": 0}}),
    ])  # fmt: skip


def test_manual_mode_stops_after_rejected_slot(api: APIClient, fake: MagicMock) -> None:
    fake.set_mode.return_value = {"set_result": False}
    body = {"mode": "manual", "slots": [slot(index=0), slot(index=1)]}
    res = post(api, "device-mode", make_device(), body).json()
    assert res["set_result"] is False
    assert res["slots"] == [{"index": 0, "set_result": False}]
    assert fake.set_mode.call_count == 1


def test_e_mini_manual_needs_action(api: APIClient, fake: MagicMock) -> None:
    mini = make_device(model="VenusEmini", firmware=100)
    assert post(api, "device-mode", mini, {"mode": "manual", "slots": [slot()]}).status_code == 400
    res = post(api, "device-mode", mini, {"mode": "manual", "slots": [slot(action="discharge")]})
    assert res.status_code == 200
    assert fake.set_mode.call_args.args[0]["manual_cfg"]["manual_set"] == 2


@pytest.mark.parametrize(
    "body",
    [
        {"mode": "turbo"},
        {"mode": "auto", "power_w": 100},  # field from another mode
        {"mode": "passive", "power_w": 100},  # missing countdown
        {"mode": "passive", "power_w": 9999, "countdown_s": 60},  # over the power cap
        {"mode": "passive", "power_w": 100, "countdown_s": 0},
        {"mode": "manual", "slots": []},
        {"mode": "manual", "slots": [slot(start="8:30")]},  # not hh:mm
        {"mode": "manual", "slots": [slot(start="25:00")]},
        {"mode": "manual", "slots": [slot(end="08:30")]},  # start == end
        {"mode": "manual", "slots": [slot(weekdays=[])]},  # enabled with no days
        {"mode": "manual", "slots": [slot(weekdays=["funday"])]},
        {"mode": "manual", "slots": [slot(index=0), slot(index=0)]},  # duplicate index
        {"mode": "manual", "slots": [slot(index=10)]},  # beyond 10 slots
        {"mode": "manual", "slots": [slot(action="charge")]},  # action is E mini only
        {"mode": "manual", "slots": [slot(index=i) for i in range(11)]},
    ],
)
def test_invalid_mode_bodies_never_reach_device(
    api: APIClient, fake: MagicMock, body: dict[str, Any]
) -> None:
    res = post(api, "device-mode", make_device(), body)
    assert res.status_code == 400, res.json()
    assert res.json()["code"] == "invalid"
    assert_no_writes(fake)


def test_mode_write_timeout_is_504_and_not_retried(api: APIClient, fake: MagicMock) -> None:
    fake.set_mode.side_effect = DeviceTimeout("ES.SetMode")
    res = post(api, "device-mode", make_device(), {"mode": "auto"})
    assert res.status_code == 504
    assert fake.set_mode.call_count == 1


def test_writes_are_rate_limited_per_device(api: APIClient, fake: MagicMock) -> None:
    a, b = make_device(), make_device(name="Other")
    assert post(api, "device-mode", a, {"mode": "auto"}).status_code == 200
    second = post(api, "device-led", a, {"on": True})
    assert second.status_code == 429
    assert second.json()["code"] == "throttled"
    assert post(api, "device-mode", b, {"mode": "ai"}).status_code == 200  # other device is fine
    fake.set_led.assert_not_called()


# --- system settings ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "body", "method", "arg"),
    [
        ("device-dod", {"value": 30}, "set_dod", 30),
        ("device-dod", {"value": 88}, "set_dod", 88),
        ("device-led", {"on": False}, "set_led", False),
        ("device-ble-adv", {"on": True}, "set_ble_advertising", True),
        ("device-power-version", {"watts": 2500}, "set_power_version", 2500),
    ],
)
def test_settings_happy_path(
    api: APIClient, fake: MagicMock, name: str, body: dict[str, Any], method: str, arg: Any
) -> None:
    res = post(api, name, make_device(), body)
    assert res.status_code == 200
    assert res.json() == {"set_result": True}
    getattr(fake, method).assert_called_once_with(arg)


@pytest.mark.parametrize(
    ("name", "body"),
    [
        ("device-dod", {"value": 29}),
        ("device-dod", {"value": 89}),
        ("device-dod", {}),
        ("device-led", {"on": "maybe"}),
        ("device-power-version", {"watts": 1000}),
    ],
)
def test_settings_validation(api: APIClient, fake: MagicMock, name: str, body: Any) -> None:
    assert post(api, name, make_device(), body).status_code == 400
    assert_no_writes(fake)


def test_settings_unsupported_on_old_firmware(api: APIClient, fake: MagicMock) -> None:
    old = make_device(firmware=149)
    res = post(api, "device-dod", old, {"value": 50})
    assert res.status_code == 404
    assert res.json()["code"] == "unsupported"
    assert_no_writes(fake)


def test_e_mini_settings(api: APIClient, fake: MagicMock) -> None:
    mini = make_device(model="Venus E mini", firmware=100)
    assert post(api, "device-dod", mini, {"value": 50}).status_code == 200
    cache.clear()
    res = post(api, "device-power-version", mini, {"watts": 800})
    assert res.status_code == 404  # Set.Ver isn't listed for E mini
    fake.set_power_version.assert_not_called()


def test_set_result_false_is_reported(api: APIClient, fake: MagicMock) -> None:
    fake.set_led.return_value = {"set_result": False}
    assert post(api, "device-led", make_device(), {"on": True}).json() == {"set_result": False}


# --- factory reset ------------------------------------------------------------------------------


def test_factory_reset_requires_exact_name(api: APIClient, fake: MagicMock) -> None:
    device = make_device(name="Home")
    for bad in (
        {"type": 1},
        {"type": 1, "confirm_name": "home"},
        {"type": 3, "confirm_name": "Home"},
    ):
        assert post(api, "device-factory-reset", device, bad).status_code == 400
    fake.reset_factory.assert_not_called()
    res = post(api, "device-factory-reset", device, {"type": 2, "confirm_name": "Home"})
    assert res.status_code == 200
    fake.reset_factory.assert_called_once_with(2, confirmed=True)


@pytest.mark.parametrize(("model", "fw"), [("VenusC", 120), ("VenusEmini", 200)])
def test_factory_reset_unsupported(api: APIClient, fake: MagicMock, model: str, fw: int) -> None:
    device = make_device(model=model, firmware=fw)
    res = post(api, "device-factory-reset", device, {"type": 1, "confirm_name": "Home"})
    assert res.status_code == 404
    fake.reset_factory.assert_not_called()


def test_get_is_not_allowed_on_write_endpoints(api: APIClient, fake: MagicMock) -> None:
    device = make_device()
    for name in ("device-dod", "device-led", "device-factory-reset"):
        assert api.get(reverse(name, args=[device.pk])).status_code == 405
    assert_no_writes(fake)
