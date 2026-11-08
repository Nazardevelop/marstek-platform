"""Serializers: typed DTOs + validators (like a TS interface with a Zod/Angular-forms validator).

Output serializers document the response shape for OpenAPI, so the FE can generate TS types.
"""

from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from devices import services
from devices.models import Device


class CapabilitiesSerializer(serializers.Serializer[Any]):
    pv = serializers.BooleanField()
    system_settings = serializers.BooleanField()
    power_version = serializers.BooleanField()
    factory_reset = serializers.BooleanField()
    manual_slots = serializers.IntegerField()
    manual_action = serializers.BooleanField()


class DeviceSerializer(serializers.ModelSerializer[Device]):
    online = serializers.BooleanField(read_only=True)
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            "id", "name", "host", "port", "model", "firmware", "ble_mac", "wifi_mac",
            "last_seen", "online", "capabilities",
        ]  # fmt: skip
        read_only_fields = ["model", "firmware", "ble_mac", "wifi_mac", "last_seen"]

    @extend_schema_field(CapabilitiesSerializer)
    def get_capabilities(self, obj: Device) -> dict[str, Any]:
        return services.capabilities(obj).as_dict()

    def validate_port(self, value: int) -> int:
        if not 1 <= value <= 65535:
            raise serializers.ValidationError("Port must be 1-65535")
        return value


# --- status --------------------------------------------------------------------------------------


class _Freshness(serializers.Serializer[Any]):
    fetched_at = serializers.DateTimeField()
    stale = serializers.BooleanField(help_text="True when the device is unreachable (cached data)")


class BatterySerializer(serializers.Serializer[Any]):
    soc_pct = serializers.FloatField(allow_null=True)
    charge_allowed = serializers.BooleanField(allow_null=True)
    discharge_allowed = serializers.BooleanField(allow_null=True)
    temperature_c = serializers.FloatField(allow_null=True)
    remaining_wh = serializers.FloatField(allow_null=True)
    rated_wh = serializers.FloatField(allow_null=True)


class PowerSerializer(serializers.Serializer[Any]):
    pv_w = serializers.FloatField(allow_null=True)
    grid_w = serializers.FloatField(allow_null=True)
    offgrid_w = serializers.FloatField(allow_null=True)
    battery_w = serializers.FloatField(allow_null=True)


class EnergySerializer(serializers.Serializer[Any]):
    pv_total_wh = serializers.FloatField(allow_null=True)
    grid_import_wh = serializers.FloatField(allow_null=True)
    grid_export_wh = serializers.FloatField(allow_null=True)
    load_total_wh = serializers.FloatField(allow_null=True)


class CtSerializer(serializers.Serializer[Any]):
    connected = serializers.BooleanField()
    phase_a_w = serializers.FloatField(allow_null=True)
    phase_b_w = serializers.FloatField(allow_null=True)
    phase_c_w = serializers.FloatField(allow_null=True)
    total_w = serializers.FloatField(allow_null=True)
    import_wh = serializers.FloatField(allow_null=True)
    export_wh = serializers.FloatField(allow_null=True)


class PvInputSerializer(serializers.Serializer[Any]):
    input = serializers.IntegerField()
    power_w = serializers.FloatField(allow_null=True)
    voltage_v = serializers.FloatField(allow_null=True)
    current_a = serializers.FloatField(allow_null=True)
    active = serializers.BooleanField()


class StatusSerializer(_Freshness):
    battery = BatterySerializer()
    power = PowerSerializer()
    energy = EnergySerializer()
    system_soc_pct = serializers.FloatField(allow_null=True)
    system_capacity_wh = serializers.FloatField(allow_null=True)
    ct = CtSerializer()
    mode = serializers.ChoiceField(
        choices=["auto", "ai", "manual", "passive", "ups"], allow_null=True
    )
    pv = PvInputSerializer(many=True, allow_null=True, help_text="null when the model has no PV")


class WifiSerializer(serializers.Serializer[Any]):
    ssid = serializers.CharField(allow_null=True)
    rssi_dbm = serializers.FloatField(allow_null=True)
    ip = serializers.CharField(allow_null=True)
    gateway = serializers.CharField(allow_null=True)
    netmask = serializers.CharField(allow_null=True)
    dns = serializers.CharField(allow_null=True)
    mac = serializers.CharField(allow_null=True)


class BluetoothSerializer(serializers.Serializer[Any]):
    state = serializers.CharField(allow_null=True)
    mac = serializers.CharField(allow_null=True)


class NetworkSerializer(_Freshness):
    wifi = WifiSerializer()
    bluetooth = BluetoothSerializer()
