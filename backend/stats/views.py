from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from devices.models import Device
from stats import services
from stats.serializers import (
    DailyEnergyQuerySerializer,
    DailyEnergySerializer,
    HistoryQuerySerializer,
    HistorySerializer,
)


class HistoryView(APIView):
    @extend_schema(parameters=[HistoryQuerySerializer], responses=HistorySerializer)
    def get(self, request: Request, device_id: int) -> Response:
        """Bucketed averages for charts (24h → 5 min, 7d → 30 min, 30d → 2 h buckets)."""
        device = get_object_or_404(Device, pk=device_id)
        query = HistoryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        return Response(services.history(device, data["range"], data["metrics"]))


class DailyEnergyView(APIView):
    @extend_schema(
        parameters=[DailyEnergyQuerySerializer], responses=DailyEnergySerializer(many=True)
    )
    def get(self, request: Request, device_id: int) -> Response:
        """Energy per local day (Wh), from the device's cumulative counters. Oldest first."""
        device = get_object_or_404(Device, pk=device_id)
        query = DailyEnergyQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(services.daily_energy(device, query.validated_data["days"]))
