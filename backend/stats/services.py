"""History: record polls, query bucketed series and daily energy, and enforce retention."""

import logging
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Any, cast

from django.db.models import Max, Min
from django.db.models.functions import TruncDate
from django.utils import timezone

from devices.models import Device
from stats.models import COUNTERS, INSTANT_METRICS, Sample

logger = logging.getLogger(__name__)

# range → (window, bucket size). Keeps every chart at roughly 300 points.
RANGES: dict[str, tuple[timedelta, timedelta]] = {
    "24h": (timedelta(hours=24), timedelta(minutes=5)),
    "7d": (timedelta(days=7), timedelta(minutes=30)),
    "30d": (timedelta(days=30), timedelta(hours=2)),
}
FULL_RESOLUTION = timedelta(days=7)
THIN_BUCKET = timedelta(minutes=5)
KEEP_FOR = timedelta(days=90)


def record_sample(device: Device, status: dict[str, Any]) -> Sample | None:
    """Store a live status read. Stale (cached) reads are skipped so history stays honest."""
    if status.get("stale"):
        return None
    power, energy = status.get("power", {}), status.get("energy", {})
    return Sample.objects.create(
        device=device,
        recorded_at=timezone.now(),
        soc_pct=status.get("battery", {}).get("soc_pct"),
        battery_w=power.get("battery_w"),
        pv_w=power.get("pv_w"),
        grid_w=power.get("grid_w"),
        offgrid_w=power.get("offgrid_w"),
        ct_total_w=(status.get("ct") or {}).get("total_w"),
        pv_total_wh=energy.get("pv_total_wh"),
        grid_import_wh=energy.get("grid_import_wh"),
        grid_export_wh=energy.get("grid_export_wh"),
        load_total_wh=energy.get("load_total_wh"),
    )


def _bucket_start(ts: datetime, size: timedelta) -> datetime:
    seconds = int(size.total_seconds())
    epoch = int(ts.timestamp())
    return datetime.fromtimestamp(epoch - epoch % seconds, tz=ts.tzinfo)


def history(device: Device, range_key: str, metrics: list[str]) -> dict[str, Any]:
    """Average each metric per bucket. Empty buckets are left out (the chart draws a gap)."""
    window, bucket = RANGES[range_key]
    since = timezone.now() - window
    rows = (
        Sample.objects.filter(device=device, recorded_at__gte=since)
        .order_by("recorded_at")
        .values_list("recorded_at", *metrics)
    )
    sums: dict[datetime, list[float]] = {}
    counts: dict[datetime, list[int]] = {}
    for recorded_at, *values in rows.iterator():
        key = _bucket_start(recorded_at, bucket)
        s = sums.setdefault(key, [0.0] * len(metrics))
        c = counts.setdefault(key, [0] * len(metrics))
        for i, value in enumerate(values):
            if value is not None:
                s[i] += value
                c[i] += 1
    points = [
        {
            "t": key.isoformat(),
            **{
                m: round(sums[key][i] / counts[key][i], 2) if counts[key][i] else None
                for i, m in enumerate(metrics)
            },
        }
        for key in sorted(sums)
    ]
    return {
        "range": range_key,
        "bucket_s": int(bucket.total_seconds()),
        "metrics": metrics,
        "points": points,
    }


def daily_energy(device: Device, days: int) -> list[dict[str, Any]]:
    """Energy per local day = max - min of each cumulative counter within that day.

    Days with no samples are returned with nulls so the bar chart keeps a steady x-axis.
    """
    tz = timezone.get_current_timezone()
    today = timezone.localdate()
    first = today - timedelta(days=days - 1)
    since = datetime.combine(first, datetime.min.time(), tzinfo=tz)
    aggregates: dict[str, Any] = {}
    for c in COUNTERS:
        aggregates[f"{c}__max"] = Max(c)
        aggregates[f"{c}__min"] = Min(c)
    rows = (
        Sample.objects.filter(device=device, recorded_at__gte=since)
        .annotate(day=TruncDate("recorded_at", tzinfo=tz))
        .values("day")
        .annotate(**aggregates)
    )
    by_day: dict[date, dict[str, Any]] = defaultdict(dict)
    for row in cast(Iterable[dict[str, Any]], rows):
        for c in COUNTERS:
            hi, lo = row[f"{c}__max"], row[f"{c}__min"]
            # A counter that went down (device reset) gives no reliable delta for that day.
            by_day[row["day"]][c] = (
                round(hi - lo, 1) if hi is not None and lo is not None and hi >= lo else None
            )
    names = {
        "pv_total_wh": "pv_wh",
        "grid_import_wh": "grid_import_wh",
        "grid_export_wh": "grid_export_wh",
        "load_total_wh": "load_wh",
    }
    result = []
    for offset in range(days):
        day = first + timedelta(days=offset)
        values = by_day.get(day, {})
        result.append({"date": day.isoformat(), **{names[c]: values.get(c) for c in COUNTERS}})
    return result


def apply_retention(now: datetime | None = None) -> dict[str, int]:
    """Keep full resolution for 7 days, one sample per 5 min after that, nothing after 90 days."""
    now = now or timezone.now()
    expired, _ = Sample.objects.filter(recorded_at__lt=now - KEEP_FOR).delete()

    seen: set[tuple[int, datetime]] = set()
    drop: list[int] = []
    old = (
        Sample.objects.filter(recorded_at__lt=now - FULL_RESOLUTION)
        .order_by("device_id", "recorded_at")
        .values_list("id", "device_id", "recorded_at")
    )
    for pk, device_id, recorded_at in old.iterator():
        key = (device_id, _bucket_start(recorded_at, THIN_BUCKET))
        if key in seen:
            drop.append(pk)
        else:
            seen.add(key)
    thinned = 0
    for i in range(0, len(drop), 500):  # stay under SQLite's variable limit
        thinned += Sample.objects.filter(pk__in=drop[i : i + 500]).delete()[0]
    if expired or thinned:
        logger.info("retention: deleted %d expired, thinned %d", expired, thinned)
    return {"expired": expired, "thinned": thinned}


__all__ = ["COUNTERS", "INSTANT_METRICS", "RANGES", "apply_retention", "daily_energy", "history"]
