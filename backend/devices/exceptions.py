"""One place that turns exceptions into the API error envelope: {code, message, detail?}.

Like an Angular HttpInterceptor, but on the server side: every view's errors pass through here.
"""

from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from devices.marstek.exceptions import DeviceRpcError, DeviceTimeout, UnsupportedFeature

JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602


def _envelope(code: str, message: str, http_status: int, detail: Any = None) -> Response:
    body: dict[str, Any] = {"code": code, "message": message}
    if detail is not None:
        body["detail"] = detail
    return Response(body, status=http_status)


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DeviceTimeout):
        return _envelope(
            "device_unreachable", "Device did not respond", status.HTTP_504_GATEWAY_TIMEOUT
        )
    if isinstance(exc, UnsupportedFeature):
        return _envelope("unsupported", str(exc) or "Not supported", status.HTTP_404_NOT_FOUND)
    if isinstance(exc, DeviceRpcError):
        rpc = {"rpc_code": exc.code, "rpc_message": exc.message}
        if exc.code == JSONRPC_METHOD_NOT_FOUND:
            return _envelope("unsupported", exc.message, status.HTTP_404_NOT_FOUND, rpc)
        if exc.code == JSONRPC_INVALID_PARAMS:
            return _envelope("invalid_params", exc.message, status.HTTP_400_BAD_REQUEST, rpc)
        return _envelope("device_error", exc.message, status.HTTP_502_BAD_GATEWAY, rpc)

    response = exception_handler(exc, context)
    if response is None:
        return None  # unexpected error: Django returns a 500
    # Django's own Http404/PermissionDenied have no DRF `default_code`.
    if isinstance(exc, Http404):
        code = "not_found"
    elif isinstance(exc, DjangoPermissionDenied):
        code = "permission_denied"
    else:
        code = getattr(exc, "default_code", "error")
    data = response.data
    if isinstance(data, dict) and set(data) == {"detail"}:
        return _envelope(str(code), str(data["detail"]), response.status_code)
    # Validation errors: field-level messages go in `detail`.
    return _envelope(str(code), "Invalid request", response.status_code, data)
