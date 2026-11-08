"""Thin views: validate → call one service → respond. Errors go through devices.exceptions."""

from collections.abc import Callable
from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from devices import control, services
from devices.control_serializers import (
    DodSerializer,
    FactoryResetSerializer,
    ModeStatusSerializer,
    ModeWriteResultSerializer,
    PowerVersionSerializer,
    SetModeSerializer,
    SetResultSerializer,
    ToggleSerializer,
)
from devices.models import Device
from devices.serializers import DeviceSerializer, NetworkSerializer, StatusSerializer


class HealthSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.CharField()


class HealthView(APIView):
    """Liveness check for the API itself (does not touch the device)."""

    @extend_schema(responses=HealthSerializer)
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class DeviceListView(APIView):
    @extend_schema(responses=DeviceSerializer(many=True))
    def get(self, request: Request) -> Response:
        services.ensure_default_device()
        return Response(DeviceSerializer(Device.objects.all(), many=True).data)


class DeviceDiscoverView(APIView):
    @extend_schema(request=None, responses=DeviceSerializer(many=True))
    def post(self, request: Request) -> Response:
        """Broadcast on the LAN (~2 s) and register every device that answers."""
        return Response(DeviceSerializer(services.discover(), many=True).data)


class DeviceDetailView(APIView):
    @extend_schema(responses=DeviceSerializer)
    def get(self, request: Request, device_id: int) -> Response:
        """Device info + capabilities. Re-reads model/firmware; if offline, returns stored info."""
        device = services.refresh_info(get_object_or_404(Device, pk=device_id))
        return Response(DeviceSerializer(device).data)

    @extend_schema(request=DeviceSerializer, responses=DeviceSerializer)
    def patch(self, request: Request, device_id: int) -> Response:
        """Rename the device or change the address the backend uses."""
        device = get_object_or_404(Device, pk=device_id)
        serializer = DeviceSerializer(device, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DeviceStatusView(APIView):
    @extend_schema(responses=StatusSerializer)
    def get(self, request: Request, device_id: int) -> Response:
        """Live dashboard data. `stale: true` = device unreachable, showing last-known values."""
        device = get_object_or_404(Device, pk=device_id)
        return Response(services.get_status(device))


class DeviceNetworkView(APIView):
    @extend_schema(responses=NetworkSerializer)
    def get(self, request: Request, device_id: int) -> Response:
        device = get_object_or_404(Device, pk=device_id)
        return Response(services.get_network(device))


# --- control (⚠️ hardware writes) ----------------------------------------------------------------


class DeviceModeView(APIView):
    @extend_schema(responses=ModeStatusSerializer)
    def get(self, request: Request, device_id: int) -> Response:
        device = get_object_or_404(Device, pk=device_id)
        return Response(control.get_mode(device))

    @extend_schema(request=SetModeSerializer, responses=ModeWriteResultSerializer)
    def post(self, request: Request, device_id: int) -> Response:
        """Set the operating mode. Manual mode programs each slot with its own SetMode call."""
        device = get_object_or_404(Device, pk=device_id)
        caps = services.capabilities(device)
        serializer = SetModeSerializer(data=request.data, context={"capabilities": caps})
        serializer.is_valid(raise_exception=True)
        return Response(control.set_mode(device, serializer.validated_data))


def _setting_view(
    serializer_class: type[serializers.Serializer[Any]],
    action: Callable[[Device, Any], dict[str, Any]],
    field: str,
    summary: str,
) -> type[APIView]:
    """Small factory: the four settings endpoints differ only in body and service call."""

    class SettingView(APIView):
        @extend_schema(request=serializer_class, responses=SetResultSerializer, summary=summary)
        def post(self, request: Request, device_id: int) -> Response:
            device = get_object_or_404(Device, pk=device_id)
            serializer = serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(action(device, serializer.validated_data[field]))

    SettingView.__name__ = f"{serializer_class.__name__.removesuffix('Serializer')}SettingView"
    return SettingView


DodView = _setting_view(DodSerializer, control.set_dod, "value", "Set depth of discharge")
LedView = _setting_view(ToggleSerializer, control.set_led, "on", "Turn the LED on/off")
BleAdvView = _setting_view(
    ToggleSerializer, control.set_ble_advertising, "on", "Bluetooth advertising on/off"
)
PowerVersionView = _setting_view(
    PowerVersionSerializer, control.set_power_version, "watts", "Set the power version"
)


class FactoryResetView(APIView):
    @extend_schema(request=FactoryResetSerializer, responses=SetResultSerializer)
    def post(self, request: Request, device_id: int) -> Response:
        """⚠️ Factory reset. `confirm_name` must exactly match the device name."""
        device = get_object_or_404(Device, pk=device_id)
        serializer = FactoryResetSerializer(data=request.data, context={"device_name": device.name})
        serializer.is_valid(raise_exception=True)
        return Response(control.factory_reset(device, serializer.validated_data["type"]))
