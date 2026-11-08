import pytest
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from devices.exceptions import api_exception_handler
from devices.marstek.exceptions import DeviceRpcError, DeviceTimeout, UnsupportedFeature


def test_health() -> None:
    response = APIClient().get(reverse("health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("exc", "http_status", "code"),
    [
        (DeviceTimeout(), 504, "device_unreachable"),
        (UnsupportedFeature("PV needs Venus A/D"), 404, "unsupported"),
        (DeviceRpcError(-32601, "Method not found"), 404, "unsupported"),
        (DeviceRpcError(-32602, "Invalid params"), 400, "invalid_params"),
        (DeviceRpcError(-32603, "Internal error"), 502, "device_error"),
    ],
)
def test_device_errors_map_to_envelope(exc: Exception, http_status: int, code: str) -> None:
    response = api_exception_handler(exc, {})
    assert response is not None
    assert response.status_code == http_status
    assert response.data["code"] == code
    assert "message" in response.data


def test_validation_error_keeps_field_detail() -> None:
    response = api_exception_handler(ValidationError({"value": ["Out of range"]}), {})
    assert response is not None
    assert response.status_code == 400
    assert response.data["code"] == "invalid"
    assert response.data["detail"] == {"value": ["Out of range"]}
