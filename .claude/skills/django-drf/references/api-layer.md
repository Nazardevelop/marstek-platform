# Models, serializers, views, URLs, errors

## Serializer (validation boundary ≈ typed DTO + validator)
```python
class SetModeSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["Auto", "AI", "Manual", "Passive"])
```
- Plain `Serializer` for device commands (no model). `ModelSerializer` for DB-backed resources.
- Range checks via `IntegerField(min_value=..., max_value=...)` or `validate_<field>`.

## View (thin)
```python
class DeviceModeView(APIView):
    def get(self, request: Request, device_id: int) -> Response:
        return Response(services.get_mode(device_id))

    def post(self, request: Request, device_id: int) -> Response:
        s = SetModeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = services.set_mode(device_id, s.validated_data["mode"])
        return Response(result, status=status.HTTP_200_OK)
```
- `APIView` for device actions (RPC-ish), `ModelViewSet` + router for CRUD resources (e.g. history).
- Prefer `ListAPIView` with filtering + pagination for stats history; never return unbounded querysets.

## URLs
```python
urlpatterns = [path("devices/<int:device_id>/mode/", DeviceModeView.as_view(), name="device-mode")]
```
Trailing slashes, kebab-case `name`s, use `reverse()` in tests.

## Errors (one place)
```python
def api_exception_handler(exc, context):
    if isinstance(exc, DeviceTimeout):
        return Response({"detail": "Device did not respond"}, status=504)
    if isinstance(exc, DeviceRpcError):
        return Response({"detail": exc.message, "code": exc.code}, status=502)
    return exception_handler(exc, context)
```

## Models (stats)
```python
class BatteryReading(models.Model):
    device_id = models.IntegerField()
    recorded_at = models.DateTimeField(db_index=True)
    soc = models.PositiveSmallIntegerField()
    class Meta:
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["device_id", "recorded_at"])]
```
Use timezone-aware datetimes (`django.utils.timezone.now()`), `USE_TZ = True`.
