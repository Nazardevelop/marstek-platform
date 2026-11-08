"""Request validation for hardware writes. Nothing reaches the device unless it passes here.

Capability checks (slot count, E mini `action`) need the device, so views pass it in `context`.
"""

import re
from typing import Any

from rest_framework import serializers

from devices.capabilities import Capabilities
from devices.marstek.client import DOD_MAX, DOD_MIN, POWER_VERSIONS

WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # bit0 … bit6 of week_set
MODES = ["auto", "ai", "manual", "passive", "ups"]
MANUAL_ACTIONS = ["disable", "charge", "discharge", "auto"]  # manual_set 0..3 (E mini)
# Inferred: the spec gives no power limits or sign convention, so cap at the largest
# power version (2500 W) in either direction.
MAX_POWER_W = 2500
MAX_COUNTDOWN_S = 24 * 3600
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _power_field(**kwargs: Any) -> serializers.IntegerField:
    return serializers.IntegerField(min_value=-MAX_POWER_W, max_value=MAX_POWER_W, **kwargs)


class TimeField(serializers.CharField):
    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data)
        if not _HHMM.match(value):
            raise serializers.ValidationError("Use 24h hh:mm, e.g. 08:30")
        return value


class ManualSlotSerializer(serializers.Serializer[Any]):
    index = serializers.IntegerField(min_value=0, help_text="Slot number (0-9, E mini 0-5)")
    start = TimeField()
    end = TimeField()
    weekdays = serializers.ListField(
        child=serializers.ChoiceField(choices=WEEKDAYS), allow_empty=True
    )
    power_w = _power_field()
    enabled = serializers.BooleanField()
    action = serializers.ChoiceField(
        choices=MANUAL_ACTIONS, required=False, help_text="E mini only"
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["enabled"] and not attrs["weekdays"]:
            raise serializers.ValidationError({"weekdays": "Pick at least one day"})
        if attrs["start"] == attrs["end"]:
            raise serializers.ValidationError({"end": "End time must differ from start"})
        attrs["weekdays"] = sorted(set(attrs["weekdays"]), key=WEEKDAYS.index)
        return attrs


class SetModeSerializer(serializers.Serializer[Any]):
    """One body for every mode; fields that don't belong to the chosen mode are rejected."""

    mode = serializers.ChoiceField(choices=MODES)
    power_w = _power_field(required=False, help_text="passive only")
    countdown_s = serializers.IntegerField(
        min_value=1, max_value=MAX_COUNTDOWN_S, required=False, help_text="passive only"
    )
    slots = ManualSlotSerializer(many=True, required=False, help_text="manual only")

    _FIELDS_BY_MODE = {"passive": {"power_w", "countdown_s"}, "manual": {"slots"}}

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        mode = attrs["mode"]
        allowed = self._FIELDS_BY_MODE.get(mode, set())
        given = set(attrs) - {"mode"}
        if extra := given - allowed:
            raise serializers.ValidationError({f: f"Not used by {mode} mode" for f in extra})
        if missing := allowed - given:
            raise serializers.ValidationError({f: "This field is required." for f in missing})
        if mode == "manual":
            self._validate_slots(attrs["slots"])
        return attrs

    def _validate_slots(self, slots: list[dict[str, Any]]) -> None:
        caps: Capabilities = self.context["capabilities"]
        if not slots:
            raise serializers.ValidationError({"slots": "Send at least one slot"})
        if len(slots) > caps.manual_slots:
            raise serializers.ValidationError({"slots": f"At most {caps.manual_slots} slots"})
        indexes = [s["index"] for s in slots]
        if len(set(indexes)) != len(indexes):
            raise serializers.ValidationError({"slots": "Slot indexes must be unique"})
        if max(indexes) >= caps.manual_slots:
            raise serializers.ValidationError(
                {"slots": f"Slot index must be 0-{caps.manual_slots - 1}"}
            )
        has_action = [("action" in s) for s in slots]
        if caps.manual_action and not all(has_action):
            raise serializers.ValidationError({"slots": "This model needs `action` per slot"})
        if not caps.manual_action and any(has_action):
            raise serializers.ValidationError({"slots": "`action` is only for Venus E mini"})


class DodSerializer(serializers.Serializer[Any]):
    value = serializers.IntegerField(min_value=DOD_MIN, max_value=DOD_MAX)


class ToggleSerializer(serializers.Serializer[Any]):
    on = serializers.BooleanField()


class PowerVersionSerializer(serializers.Serializer[Any]):
    watts = serializers.ChoiceField(choices=sorted(POWER_VERSIONS))


class FactoryResetSerializer(serializers.Serializer[Any]):
    type = serializers.ChoiceField(
        choices=[(1, "Reset and clear accumulated data"), (2, "Reset and keep accumulated data")]
    )
    confirm_name = serializers.CharField(help_text="Must exactly match the device name")

    def validate_confirm_name(self, value: str) -> str:
        if value != self.context["device_name"]:
            raise serializers.ValidationError("Type the exact device name to confirm")
        return value


# --- responses ----------------------------------------------------------------------------------


class SetResultSerializer(serializers.Serializer[Any]):
    set_result = serializers.BooleanField()


class SlotResultSerializer(serializers.Serializer[Any]):
    index = serializers.IntegerField()
    set_result = serializers.BooleanField()


class ModeWriteResultSerializer(SetResultSerializer):
    slots = SlotResultSerializer(many=True, required=False)
    current = serializers.DictField(
        allow_null=True, help_text="Mode read back after the write (ES.GetMode)"
    )


class ModeStatusSerializer(serializers.Serializer[Any]):
    mode = serializers.ChoiceField(choices=MODES, allow_null=True)
    grid_w = serializers.FloatField(allow_null=True)
    offgrid_w = serializers.FloatField(allow_null=True)
    soc_pct = serializers.FloatField(allow_null=True)
    ct = serializers.DictField(allow_null=True, help_text="CT meter; only in auto/ai mode")
    fetched_at = serializers.DateTimeField()
    stale = serializers.BooleanField()
