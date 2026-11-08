"""`manage.py poll_device`: read every device's status on an interval and store a Sample.

Runs as its own process (its own docker-compose service), like a long-running Node worker.
Reads only: this command never sends a write to the device.
"""

import logging
import signal
import time
from types import FrameType
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from devices import services
from devices.marstek.exceptions import MarstekError
from devices.models import Device
from stats import services as stats

logger = logging.getLogger(__name__)
RETENTION_EVERY_S = 3600


class Command(BaseCommand):
    help = "Poll device status on an interval and store history samples."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--interval", type=float, default=10.0, help="Seconds between polls")
        parser.add_argument("--once", action="store_true", help="Poll once and exit")

    def handle(self, *args: Any, **options: Any) -> None:
        interval: float = options["interval"]
        self._running = True
        signal.signal(signal.SIGTERM, self._stop)  # `docker stop` sends SIGTERM
        services.ensure_default_device()
        last_retention = 0.0
        self.stdout.write(f"Polling every {interval:g}s (Ctrl+C to stop)")
        while self._running:
            started = time.monotonic()
            stored = self.poll_all()
            if started - last_retention >= RETENTION_EVERY_S:
                stats.apply_retention()
                last_retention = started
            if options["once"]:
                self.stdout.write(f"Stored {stored} sample(s)")
                return
            self._sleep(interval - (time.monotonic() - started))

    def poll_all(self) -> int:
        stored = 0
        for device in Device.objects.all():
            try:
                status = services.get_status(device)  # also refreshes the last-known cache
            except MarstekError as exc:
                logger.warning("device %s: %s", device.pk, exc)
                continue
            if stats.record_sample(device, status) is not None:
                stored += 1
        return stored

    def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + max(seconds, 0)
        while self._running and time.monotonic() < end:  # wake up quickly on SIGTERM
            time.sleep(min(0.5, end - time.monotonic()))

    def _stop(self, signum: int, frame: FrameType | None) -> None:
        self._running = False
