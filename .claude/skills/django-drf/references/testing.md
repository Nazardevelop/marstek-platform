# Testing (pytest + pytest-django)

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
```

## Fixtures (≈ TestBed providers)
```python
# conftest.py
@pytest.fixture
def fake_client(monkeypatch):
    client = MagicMock(spec=MarstekClient)
    monkeypatch.setattr("devices.services.get_client", lambda: client)
    return client

@pytest.fixture
def api():
    return APIClient()
```

## API test
```python
def test_set_mode_rejects_unknown_mode(api, fake_client):
    res = api.post(reverse("device-mode", args=[0]), {"mode": "Turbo"}, format="json")
    assert res.status_code == 400
    fake_client.set_mode.assert_not_called()

def test_device_timeout_maps_to_504(api, fake_client):
    fake_client.get_battery_status.side_effect = DeviceTimeout("Bat.GetStatus")
    assert api.get(reverse("device-battery", args=[0])).status_code == 504
```
- Plain `assert`, function tests, `@pytest.mark.django_db` only when touching the DB.
- Test the client itself with a fake socket (patch `socket.socket`), never a real device.
- Cover: happy path, validation error, device timeout, device RPC error.
