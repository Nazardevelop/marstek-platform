from datetime import timedelta
from typing import Any

from django.db import models
from django.utils import timezone

ONLINE_WINDOW = timedelta(seconds=60)


class Device(models.Model):
    """A Marstek device on the LAN. Rows come from `.env` (MARSTEK_HOST) or from discovery."""

    name = models.CharField(max_length=100, default="Marstek")
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=30000)
    model = models.CharField(max_length=50, blank=True)  # e.g. "VenusC"
    firmware = models.PositiveIntegerField(null=True, blank=True)  # GetDevice `ver`
    ble_mac = models.CharField(max_length=32, blank=True)
    wifi_mac = models.CharField(max_length=32, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    # Last-known payloads per read ("status", "network"), served when the device is unreachable.
    cache = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["ble_mac"], condition=~models.Q(ble_mac=""), name="unique_ble_mac"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.host}:{self.port})"

    @property
    def online(self) -> bool:
        return self.last_seen is not None and timezone.now() - self.last_seen < ONLINE_WINDOW

    def cached(self, key: str) -> dict[str, Any] | None:
        value = self.cache.get(key)
        return value if isinstance(value, dict) else None
