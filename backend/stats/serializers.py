from typing import Any

from rest_framework import serializers

from stats.models import INSTANT_METRICS
from stats.services import RANGES


class HistoryQuerySerializer(serializers.Serializer[Any]):
    range = serializers.ChoiceField(choices=list(RANGES), default="24h")
    metrics = serializers.CharField(
        required=False, help_text=f"Comma-separated, any of: {', '.join(INSTANT_METRICS)}"
    )

    def validate_metrics(self, value: str) -> list[str]:
        metrics = [m.strip() for m in value.split(",") if m.strip()]
        if unknown := [m for m in metrics if m not in INSTANT_METRICS]:
            raise serializers.ValidationError(f"Unknown metric(s): {', '.join(unknown)}")
        return list(dict.fromkeys(metrics)) or INSTANT_METRICS

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs.setdefault("metrics", INSTANT_METRICS)
        return attrs


class DailyEnergyQuerySerializer(serializers.Serializer[Any]):
    days = serializers.IntegerField(min_value=1, max_value=90, default=7)


class HistoryPointSerializer(serializers.Serializer[Any]):
    t = serializers.DateTimeField()
    soc_pct = serializers.FloatField(allow_null=True, required=False)
    battery_w = serializers.FloatField(allow_null=True, required=False)
    pv_w = serializers.FloatField(allow_null=True, required=False)
    grid_w = serializers.FloatField(allow_null=True, required=False)
    offgrid_w = serializers.FloatField(allow_null=True, required=False)
    ct_total_w = serializers.FloatField(allow_null=True, required=False)


class HistorySerializer(serializers.Serializer[Any]):
    range = serializers.CharField()
    bucket_s = serializers.IntegerField()
    metrics = serializers.ListField(child=serializers.CharField())
    points = HistoryPointSerializer(many=True)


class DailyEnergySerializer(serializers.Serializer[Any]):
    date = serializers.DateField()
    pv_wh = serializers.FloatField(allow_null=True)
    grid_import_wh = serializers.FloatField(allow_null=True)
    grid_export_wh = serializers.FloatField(allow_null=True)
    load_wh = serializers.FloatField(allow_null=True)
