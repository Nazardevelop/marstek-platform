# Marstek Platform

A web app plus a REST API for controlling a Marstek power station on your home LAN and viewing its data.

```
React web app  ──HTTP/JSON──▶  Django REST API  ──UDP/JSON-RPC──▶  Marstek device (LAN)
```

The frontend never talks to the device directly. All device access goes through the Django API.

## Features
- Live device status: battery, PV, grid and energy-storage readings, normalized to W/Wh
- Device control: operating mode, depth of discharge, LED and BLE settings (each write asks for confirmation)
- History and daily energy charts, from a background poller that stores samples
- Capability-aware UI that hides features your model or firmware doesn't support
- AI assistant chat (currently a mock; the real Anthropic tool-use version is in progress)

## Stack
- **Frontend:** React + TypeScript, Vite, MUI, TanStack Query, Vitest
- **Backend:** Python, Django + Django REST Framework, uv, pytest, ruff, mypy
- **AI:** Anthropic Python SDK

## Prerequisites
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+ and npm
- A Marstek device with **Local API enabled** in the Marstek mobile app (default UDP port 30000)

## Setup
```bash
cp .env.example .env          # set MARSTEK_HOST, MARSTEK_PORT, SECRET_KEY, ANTHROPIC_API_KEY
```

Backend (in `backend/`):
```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver          # http://localhost:8000
uv run python manage.py poll_device        # optional: stats poller, run in a second terminal
```

Frontend (in `frontend/`):
```bash
npm install
npm run dev                                # http://localhost:5173
```

API docs (Swagger): http://localhost:8000/api/schema/swagger-ui/

## Development
| Task | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Tests | `uv run pytest` | `npm test` |
| Lint / format | `uv run ruff check . && uv run ruff format .` | `npm run lint` / `npm run format` |
| Type check | `uv run mypy .` | `npm run typecheck` |
| Regenerate API types | | `npm run gen:api` |

Tests never touch real hardware: network sockets are blocked and the device client is mocked.

### Git hooks
Commits are scanned for secrets (gitleaks), and `.env` files are blocked from being committed:
```bash
brew install gitleaks
uv tool install pre-commit && pre-commit install
```

## Safety
Write endpoints change real hardware. They are validated, rate-limited (1 write per 2 s per device) and audit-logged. A factory reset requires you to type the device name, and the AI assistant only gets read-only tools.

## Spec
Built against the Marstek Device Open API (Local API Rev 3.1.2). The spec is vendor material, so it isn't included in this repo. Get it from Marstek and put it at `docs/MarstekDeviceOpenApi.pdf`.

## Roadmap
- Real AI assistant (Anthropic tool use)
- Dockerfiles and docker-compose
