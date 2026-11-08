from datetime import date, datetime, timedelta
from io import StringIO
from typing import Any
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from devices.marstek.client import MarstekClient
from devices.marstek.exceptions import DeviceTimeout
from devices.models import Device
from devices.tests.fakes import load_doc_examples
from stats import services
from stats.models import Sample

pytestmark = pytest.mark.django_db
EXAMPLES = load_doc_examples()
WRITES = ("set_mode", "set_dod", "set_led", "set_ble_advertising", "set_power_version",
          "reset_factory")  # fmt: skip


def result(method: str) -> Any:
    return EXAMPLES[(method, "response", None)]["result"]


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    client = MagicMock(spec=MarstekClient)
    reads = {
        "Bat.GetStatus": "get_battery_status",
        "ES.GetStatus": "get_es_status",
        "EM.GetStatus": "get_em_status",
        "ES.GetMode": "get_mode",
    }
    for method, attr in reads.items():
        getattr(client, attr).return_value = result(method)
    monkeypatch.setattr("devices.services.client_for", lambda host, port: client)
    return client


@pytest.fixture
def device() -> Device:
    return Device.objects.create(name="Home", host="192.168.1.50", model="VenusC", firmware=150)


def add(device: Device, at: datetime, **values: float | None) -> Sample:
    return Sample.objects.create(device=device, recorded_at=at, **values)


# --- poller -------------------------------------------------------------------------------------


def test_poll_once_stores_normalized_sample(fake: MagicMock, device: Device) -> None:
    out = StringIO()
    call_command("poll_device", "--once", stdout=out)
    assert "Stored 1 sample" in out.getvalue()
    sample = Sample.objects.get()
    es = result("ES.GetStatus")
    assert sample.soc_pct == float(result("Bat.GetStatus")["soc"])
    assert sample.grid_import_wh == es["total_grid_input_energy"]
    assert sample.pv_total_wh == es["total_pv_energy"] * 10  # 0.01 kWh → Wh
    for write in WRITES:
        getattr(fake, write).assert_not_called()


def test_poll_skips_stale_and_unreachable(fake: MagicMock, device: Device) -> None:
    call_command("poll_device", "--once", stdout=StringIO())  # fills the cache
    fake.get_battery_status.side_effect = DeviceTimeout("Bat.GetStatus")
    call_command("poll_device", "--once", stdout=StringIO())  # stale → not stored
    Device.objects.create(name="Never seen", host="192.168.1.99")  # no cache → 504 → skipped
    call_command("poll_device", "--once", stdout=StringIO())
    assert Sample.objects.count() == 1


# --- history ------------------------------------------------------------------------------------


def test_history_buckets_and_averages(device: Device) -> None:
    now = timezone.now()
    base = services._bucket_start(now - timedelta(hours=1), timedelta(minutes=5))
    add(device, base + timedelta(seconds=10), soc_pct=50, pv_w=100)
    add(device, base + timedelta(seconds=20), soc_pct=60, pv_w=None)
    add(device, base + timedelta(minutes=5), soc_pct=70, pv_w=300)
    add(device, now - timedelta(days=2), soc_pct=1)  # outside 24h
    data = services.history(device, "24h", ["soc_pct", "pv_w"])
    assert data["bucket_s"] == 300
    assert data["points"] == [
        {"t": base.isoformat(), "soc_pct": 55.0, "pv_w": 100.0},  # None ignored in the average
        {"t": (base + timedelta(minutes=5)).isoformat(), "soc_pct": 70.0, "pv_w": 300.0},
    ]


def test_history_endpoint_validates_query(device: Device) -> None:
    api = APIClient()
    url = reverse("device-history", args=[device.pk])
    assert api.get(url, {"range": "1y"}).status_code == 400
    assert api.get(url, {"metrics": "soc_pct,secret"}).status_code == 400
    body = api.get(url, {"range": "7d", "metrics": "soc_pct,soc_pct"}).json()
    assert body["metrics"] == ["soc_pct"]
    assert api.get(url).json()["metrics"] == services.INSTANT_METRICS


# --- daily energy -------------------------------------------------------------------------------


@override_settings(TIME_ZONE="Europe/Kyiv")
def test_daily_energy_per_local_day(device: Device) -> None:
    tz = ZoneInfo("Europe/Kyiv")
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    def at(d: date, hours: float) -> datetime:
        return datetime.combine(d, datetime.min.time(), tzinfo=tz) + timedelta(hours=hours)

    add(device, at(yesterday, 1), grid_import_wh=1000, pv_total_wh=0)
    add(device, at(yesterday, 23), grid_import_wh=1500, pv_total_wh=200)
    add(device, at(today, 0.5), grid_import_wh=1600, pv_total_wh=200)  # 00:30 local = still "today"
    add(device, at(today, 0.75), grid_import_wh=1700, pv_total_wh=50)  # counter went down
    days = services.daily_energy(device, 3)
    assert [d["date"] for d in days] == [
        (today - timedelta(days=2)).isoformat(), yesterday.isoformat(), today.isoformat(),
    ]  # fmt: skip
    assert days[0]["grid_import_wh"] is None  # no samples that day
    assert (days[1]["grid_import_wh"], days[1]["pv_wh"]) == (500.0, 200.0)
    assert days[2]["grid_import_wh"] == 100.0
    assert days[2]["pv_wh"] is not None  # max-min still >= 0 here (200 vs 50)


def test_daily_energy_endpoint(device: Device) -> None:
    api = APIClient()
    url = reverse("device-energy-daily", args=[device.pk])
    assert api.get(url, {"days": 0}).status_code == 400
    assert api.get(url, {"days": 91}).status_code == 400
    assert len(api.get(url).json()) == 7


# --- retention ----------------------------------------------------------------------------------


def test_retention_thins_old_and_drops_expired(device: Device) -> None:
    now = timezone.now()
    recent = now - timedelta(days=1)
    old_bucket = services._bucket_start(now - timedelta(days=10), timedelta(minutes=5))
    for s in range(0, 60, 10):
        add(device, recent + timedelta(seconds=s))  # 6 recent: all kept
        add(device, old_bucket + timedelta(seconds=s))  # 6 old in one 5-min bucket: keep 1
    add(device, now - timedelta(days=91))  # expired
    assert services.apply_retention(now) == {"expired": 1, "thinned": 5}
    assert Sample.objects.count() == 7
    assert (
        Sample.objects.filter(recorded_at__lt=now - timedelta(days=7)).get().recorded_at
        == old_bucket
    )
