from django.db import models

from devices.models import Device


def _metric() -> models.FloatField:  # type: ignore[type-arg]
    return models.FloatField(null=True, blank=True)


class Sample(models.Model):
    """One poll of the device's live status, already normalized to %, W and Wh."""

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="samples")
    recorded_at = models.DateTimeField()

    # instantaneous
    soc_pct = _metric()
    battery_w = _metric()
    pv_w = _metric()
    grid_w = _metric()
    offgrid_w = _metric()
    ct_total_w = _metric()

    # cumulative counters (Wh); daily energy = max - min per day
    pv_total_wh = _metric()
    grid_import_wh = _metric()
    grid_export_wh = _metric()
    load_total_wh = _metric()

    class Meta:
        ordering = ["recorded_at"]
        indexes = [models.Index(fields=["device", "recorded_at"])]

    def __str__(self) -> str:
        return f"{self.device_id} @ {self.recorded_at:%Y-%m-%d %H:%M:%S}"


# Metrics the history endpoint may return (also the allowed `metrics=` values).
INSTANT_METRICS = ["soc_pct", "battery_w", "pv_w", "grid_w", "offgrid_w", "ct_total_w"]
COUNTERS = ["pv_total_wh", "grid_import_wh", "grid_export_wh", "load_total_wh"]
