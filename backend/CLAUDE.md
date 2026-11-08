# Marstek Platform: Backend

Django + Django REST Framework API that bridges the web app (HTTP/JSON) to the Marstek device (UDP JSON-RPC).
Coding conventions: follow the `django-drf` skill. Project-wide rules are in `../CLAUDE.md`.
Full plan: `~/.claude/plans/how-to-get-prev-proud-pebble.md`. Device spec: `../docs/MarstekDeviceOpenApi.md`.

## Stack
Python ≥3.12, Django 5.2 LTS, DRF, django-environ, django-cors-headers, drf-spectacular (OpenAPI),
pytest + pytest-django, ruff, mypy (strict, django-stubs + drf-stubs). Deps are managed with **uv**.

## Commands (run in `backend/`)
`uv` is like npm + nvm for Python: it installs Python itself, creates `.venv`, and locks deps in `uv.lock`.
- `uv sync`: install deps (like `npm ci`)
- `uv run python manage.py runserver`: dev server on :8000
- `uv run python manage.py migrate` / `makemigrations`
- `uv run pytest`: tests
- `uv run ruff check . && uv run ruff format .`: lint and format (like ESLint + Prettier)
- `uv run mypy .`: type check
- `uv run python manage.py poll_device [--interval 10] [--once]`: stats poller (reads only; a separate long-running process)
- API docs: http://localhost:8000/api/schema/swagger-ui/ (schema at `/api/schema/`)

## Config
Settings read the **repo-root** `.env` (`../.env`, git-ignored). The keys are listed in `../.env.example`:
`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DATABASE_URL`, `MARSTEK_HOST/PORT/TIMEOUT`,
`ANTHROPIC_API_KEY/MODEL`, `LOG_LEVEL`. Read them via `django.conf.settings` only.

## Layout
- `config/`: settings and root urls. All API routes are under `/api/v1/`.
- `devices/`: the `marstek/` package (UDP client, types, domain exceptions) plus services, views, `exceptions.py` (the API error handler).
- `stats/`: `Sample` history and the `poll_device` management command (runs as its own compose service).
- `assistant/`: Anthropic tool-use chat. **Read-only tools only**, never `Reset.Factory`. ⚠️ **Currently a MOCK** (plan step 6 skipped): `POST assistant/chat/` validates the real request contract and streams a fixed "in progress" reply.

## Endpoints so far (`/api/v1/`)
- Reads: `health/` · `devices/` (seeds the `.env` device on first call) · `devices/{id}/` (GET re-reads info + `capabilities`; PATCH name/host/port) · `devices/{id}/status/` · `devices/{id}/network/` · `GET devices/{id}/mode/`
- Stats (from the DB, not the device): `devices/{id}/history/?range=24h|7d|30d&metrics=soc_pct,pv_w,…` · `devices/{id}/energy/daily/?days=1-90`
- Assistant (MOCK): `POST assistant/chat/` `{messages:[{role,content}], context?:{route,device_id,extra}}` → `text/event-stream`: `event: delta` `{text}` …, then `event: done` `{mock:true}`. Header `X-Assistant-Mock: true`. Errors (400) are always the JSON envelope. Set `ASSISTANT_MOCK_INSTANT=true` to skip the fake typing delay.
- Writes (POST only, ⚠️ real hardware): `devices/discover/` (LAN broadcast, not a device write) · `devices/{id}/mode/` · `devices/{id}/settings/{dod,led,ble-adv,power-version}/` · `devices/{id}/factory-reset/` (`confirm_name` must equal the device name)

## Device layer
- `devices/marstek/client.py`: `MarstekClient` (the only UDP code). `client_for(host, port)` is cached per address, so each device gets one lock. Reads retry; writes never do.
- `devices/services.py`: `normalize_*` turns raw payloads into W/Wh/bool. `read_or_cached` stores the last good read in `Device.cache` and returns it with `stale: true` on timeout (504 if there's no cache).
- `devices/capabilities.py`: the support matrix as pure functions. E mini detection ("mini" in the model name) is **inferred**; check it against a real E mini.
- `devices/control.py` + `control_serializers.py`: every hardware write. The flow is serializer → capability gate (404 `unsupported`) → rate limit (1 write per 2 s per device via `cache.add`, 429 `throttled`) → audit log (`devices.audit` logger) → client.
  Manual mode sends one `ES.SetMode` per slot and stops at the first `set_result: false`. Power is capped at ±2500 W (**inferred**: the spec gives no limit or sign convention).
- Tests: `devices/tests/fakes.py` parses the spec's JSON examples. In API tests, patch `devices.services.client_for` with a `MagicMock(spec=MarstekClient)`. The autouse fixture in `conftest.py` blocks real sockets.

## Stats layer
- `stats/models.py` `Sample`: one normalized status read (instant W/% values + cumulative Wh counters). Stale reads are never stored.
- `stats/services.py`: `history` averages per bucket (24h → 5 min, 7d → 30 min, 30d → 2 h; empty buckets are left out). `daily_energy` = max − min of each counter per **local** day (`TIME_ZONE` in `.env`; a counter that went down gives `null`). `apply_retention`: full resolution for 7 days, then one per 5 min, deleted after 90 days (the poller runs it hourly).

## API rules
- No auth (LAN app). Keep `<device_id>` in URLs.
- Error envelope from `devices.exceptions.api_exception_handler`: `{code, message, detail?}`.
  `DeviceTimeout` → 504 `device_unreachable`, `UnsupportedFeature` / RPC -32601 → 404 `unsupported`,
  RPC -32602 → 400 `invalid_params`, other RPC errors → 502 `device_error`, validation → 400 with field `detail`.
- Units are normalized to W / Wh in services. Hide raw quirks (`week_set` bitmask, inverted `Ble.Adv`).
- Write endpoints use POST, strict serializer validation, logging and a rate limit. Never call them from tests (patch `devices.services.client_for`).
- Open question: the `ES.SetMode` UPS casing (`Ups` vs `UPS`). Test it once on the real device.
- Not built yet (skipped for now): the real assistant (plan step 6) and the Dockerfile + compose (step 7).
