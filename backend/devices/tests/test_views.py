"""API tests. The device client is a MagicMock fed with spec examples (no sockets)."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from devices.marstek.client import MarstekClient
from devices.marstek.exceptions import DeviceRpcError, DeviceTimeout
from devices.models import Device
from devices.tests.fakes import load_doc_examples

pytestmark = pytest.mark.django_db
EXAMPLES = load_doc_examples()


def result(method: str) -> Any:
    return EXAMPLES[(method, "response", None)]["result"]


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Every service call gets this client (like providing a mock service in TestBed)."""
    client = MagicMock(spec=MarstekClient)
    client.get_device.return_value = result("Marstek.GetDevice")
    client.get_battery_status.return_value = result("Bat.GetStatus")
    client.get_es_status.return_value = result("ES.GetStatus")
    client.get_em_status.return_value = result("EM.GetStatus")
    client.get_mode.return_value = result("ES.GetMode")
    client.get_pv_status.return_value = result("PV.GetStatus")
    client.get_wifi_status.return_value = result("Wifi.GetStatus")
    client.get_ble_status.return_value = result("BLE.GetStatus")
    monkeypatch.setattr("devices.services.client_for", lambda host, port: client)
    monkeypatch.setattr("devices.services.get_discovery_client", lambda: client)
    return client


@pytest.fixture
def device() -> Device:
    return Device.objects.create(name="Home", host="192.168.1.50", model="VenusC", firmware=150)


# --- registry -----------------------------------------------------------------------------------


@override_settings(MARSTEK_HOST="10.0.0.5", MARSTEK_PORT=30001)
def test_list_seeds_env_device(api: APIClient) -> None:
    body = api.get(reverse("device-list")).json()
    assert [(d["host"], d["port"]) for d in body] == [("10.0.0.5", 30001)]
    api.get(reverse("device-list"))
    assert Device.objects.count() == 1


def test_detail_refreshes_info_and_capabilities(api: APIClient, fake: MagicMock) -> None:
    dev = Device.objects.create(host="192.168.1.50")
    body = api.get(reverse("device-detail", args=[dev.pk])).json()
    assert body["model"] == "VenusC"
    assert body["firmware"] == result("Marstek.GetDevice")["ver"]
    assert body["online"] is True
    assert body["capabilities"]["pv"] is False
    assert body["capabilities"]["manual_slots"] == 10


def test_detail_offline_keeps_cached_info(api: APIClient, fake: MagicMock, device: Device) -> None:
    fake.get_device.side_effect = DeviceTimeout("Marstek.GetDevice")
    body = api.get(reverse("device-detail", args=[device.pk])).json()
    assert (body["model"], body["online"]) == ("VenusC", False)


def test_patch_validates_port(api: APIClient, device: Device) -> None:
    url = reverse("device-detail", args=[device.pk])
    assert api.patch(url, {"port": 70000}, format="json").status_code == 400
    res = api.patch(url, {"name": "Garage", "model": "hacked"}, format="json")
    assert res.status_code == 200
    device.refresh_from_db()
    assert (device.name, device.model) == ("Garage", "VenusC")  # model is read-only


def test_unknown_device_404(api: APIClient) -> None:
    res = api.get(reverse("device-status", args=[999]))
    assert res.status_code == 404
    assert res.json()["code"] == "not_found"


def test_discover_upserts_by_mac(api: APIClient, fake: MagicMock) -> None:
    info = result("Marstek.GetDevice")
    Device.objects.create(name="Mine", host="1.1.1.1", ble_mac=info["ble_mac"])
    fake.discover.return_value = [info, {**info, "ble_mac": "other", "ip": "192.168.1.99"}]
    body = api.post(reverse("device-discover")).json()
    assert sorted(d["host"] for d in body) == ["192.168.1.11", "192.168.1.99"]
    assert Device.objects.count() == 2
    assert Device.objects.get(ble_mac=info["ble_mac"]).name == "Mine"  # kept user's name


# --- status / network ---------------------------------------------------------------------------


def test_status_aggregate(api: APIClient, fake: MagicMock, device: Device) -> None:
    body = api.get(reverse("device-status", args=[device.pk])).json()
    assert body["stale"] is False
    assert body["battery"]["soc_pct"] == float(result("Bat.GetStatus")["soc"])
    assert body["mode"] == "auto"
    assert body["pv"] is None  # Venus C has no PV
    fake.get_pv_status.assert_not_called()
    assert set(body) >= {"power", "energy", "ct", "fetched_at"}


def test_status_includes_pv_on_venus_d(api: APIClient, fake: MagicMock, device: Device) -> None:
    device.model = "VenusD"
    device.save()
    body = api.get(reverse("device-status", args=[device.pk])).json()
    assert len(body["pv"]) == 4


def test_status_pv_method_not_found_is_treated_as_absent(
    api: APIClient, fake: MagicMock, device: Device
) -> None:
    device.model = "VenusD"
    device.save()
    fake.get_pv_status.side_effect = DeviceRpcError(-32601, "Method not found")
    assert api.get(reverse("device-status", args=[device.pk])).json()["pv"] is None


def test_status_serves_stale_cache_when_offline(
    api: APIClient, fake: MagicMock, device: Device
) -> None:
    url = reverse("device-status", args=[device.pk])
    first = api.get(url).json()
    fake.get_battery_status.side_effect = DeviceTimeout("Bat.GetStatus")
    second = api.get(url).json()
    assert second["stale"] is True
    assert second["fetched_at"] == first["fetched_at"]
    assert second["battery"] == first["battery"]


def test_status_offline_without_cache_is_504(
    api: APIClient, fake: MagicMock, device: Device
) -> None:
    fake.get_es_status.side_effect = DeviceTimeout("ES.GetStatus")
    res = api.get(reverse("device-status", args=[device.pk]))
    assert res.status_code == 504
    assert res.json()["code"] == "device_unreachable"


def test_network(api: APIClient, fake: MagicMock, device: Device) -> None:
    body = api.get(reverse("device-network", args=[device.pk])).json()
    assert body["wifi"]["ssid"] == result("Wifi.GetStatus")["ssid"]
    assert body["bluetooth"]["state"] == "connect"
    assert body["stale"] is False


def test_no_writes_happen_on_reads(api: APIClient, fake: MagicMock, device: Device) -> None:
    api.get(reverse("device-status", args=[device.pk]))
    api.get(reverse("device-network", args=[device.pk]))
    for write in ("set_mode", "set_dod", "set_led", "set_ble_advertising",
                  "set_power_version", "reset_factory"):  # fmt: skip
        getattr(fake, write).assert_not_called()
