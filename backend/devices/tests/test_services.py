"""Normalizers against the spec's real example payloads (unit conversion is the risky part)."""

from typing import Any, cast

from devices import services
from devices.marstek.types import BatteryStatus, EmStatus, EsStatus
from devices.tests.fakes import load_doc_examples

EXAMPLES = load_doc_examples()


def result(method: str) -> Any:
    return EXAMPLES[(method, "response", None)]["result"]


def test_battery_soc_accepts_string_or_number() -> None:
    raw = result("Bat.GetStatus")
    assert services.normalize_battery(raw)["soc_pct"] == float(raw["soc"])
    assert services.normalize_battery(cast(BatteryStatus, {**raw, "soc": "42"}))["soc_pct"] == 42.0


def test_es_pv_energy_converted_from_centi_kwh() -> None:
    raw = {**result("ES.GetStatus"), "total_pv_energy": 1234}  # 12.34 kWh
    es = services.normalize_es(cast(EsStatus, raw))
    assert es["energy"]["pv_total_wh"] == 12340.0
    assert es["energy"]["grid_import_wh"] == raw["total_grid_input_energy"]  # already Wh
    assert es["power"]["battery_w"] is None  # missing from the spec example


def test_em_energy_converted_from_deci_wh() -> None:
    raw = {**result("EM.GetStatus"), "input_energy": 12345, "output_energy": 10}
    ct = services.normalize_em(cast(EmStatus, raw))
    assert ct["import_wh"] == 1234.5
    assert ct["export_wh"] == 1.0
    assert ct["connected"] is (raw["ct_state"] == 1)


def test_mode_is_lowercased() -> None:
    assert services.normalize_mode(result("ES.GetMode"))["mode"] == "auto"


def test_pv_inputs_parsed_from_numbered_keys() -> None:
    pv = services.normalize_pv(result("PV.GetStatus"))
    assert [p["input"] for p in pv] == [1, 2, 3, 4]
    assert pv[0]["voltage_v"] == 10.0
    assert pv[0]["active"] is False


def test_wifi_and_ble() -> None:
    wifi = services.normalize_wifi(result("Wifi.GetStatus"))
    assert set(wifi) == {"ssid", "rssi_dbm", "ip", "gateway", "netmask", "dns", "mac"}
    assert services.normalize_ble(result("BLE.GetStatus"))["state"] == "connect"
