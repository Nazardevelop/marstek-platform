# Marstek UDP JSON-RPC client

All device I/O lives in `devices/marstek/client.py`. (Angular analogy: an injectable service wrapping
HttpClient; tests provide a fake.)

```python
class MarstekClient:
    def __init__(self, host: str, port: int, timeout: float = 2.0) -> None: ...

    def call(self, method: str, params: dict[str, object]) -> dict[str, object]:
        req_id = next(self._ids)
        payload = json.dumps({"id": req_id, "method": method, "params": params}).encode()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self.timeout)
            sock.sendto(payload, (self.host, self.port))
            try:
                data, _ = sock.recvfrom(65535)
            except TimeoutError as e:
                raise DeviceTimeout(method) from e
        msg = json.loads(data)
        if "error" in msg:
            raise DeviceRpcError(msg["error"]["code"], msg["error"]["message"])
        return msg["result"]

    # typed wrappers, one per method:
    def get_battery_status(self, device_id: int = 0) -> BatStatus: ...
    def set_mode(self, mode: Mode, device_id: int = 0) -> SetResult: ...


@lru_cache
def get_client() -> MarstekClient:
    return MarstekClient(settings.MARSTEK_HOST, settings.MARSTEK_PORT, settings.MARSTEK_TIMEOUT)
```
- Services call `get_client()`; tests patch `devices.services.get_client` (or use a fixture).
- Check response `id` matches the request id; ignore stray packets.
- Payload field names come from `docs/MarstekDeviceOpenApi.md` — grep the method card, don't invent.
- `ES.SetMode`: send only the `*_cfg` object matching `mode` (spec note).

## Write-command safety
- Validate before calling (serializer + typed wrapper accepting a `Literal`).
- `logger.info("write %s %s", method, params)` for every write.
- `Reset.Factory`: endpoint requires `{"confirm": "RESET"}`; not registered in `assistant/tools.py`.
- AI tools: read methods freely; write tools (if any) must be an explicit allowlist with validated args.
- Tests must never construct a real `MarstekClient` against a host; use a fake.
