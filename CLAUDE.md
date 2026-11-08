# Marstek Platform

A web app plus a REST API for controlling a Marstek power station and viewing its data.

```
React web app  ──HTTP/JSON──▶  Django REST API (bridge)  ──UDP/JSON-RPC──▶  Marstek device (LAN)
```
The frontend never talks to the device directly. All device access goes through the Django API.

## Goals (learning project)
1. Claude Code tooling: **hooks** for lifecycle automation, **subagents** for parallel work, **skills** for reusable prompts.
2. Learn **React + TSX** (FE) and **Python + Django** (BE).
3. Build the platform from the PDF spec: control the device and show statistics.
4. A **Dockerfile** for each of BE and FE, plus docker-compose to run both.
5. **AI assistant**: answers natural-language questions with Marstek data (Anthropic API with tool use).

## Stack
- FE: React + TypeScript (Vite)
- BE: Python + Django + Django REST Framework
- AI: `anthropic` Python SDK, default model `claude-sonnet-5-5`
- Infra: Docker, docker-compose

## Marstek API (source of truth: `docs/MarstekDeviceOpenApi.pdf`, Local API Rev 3.1.2)
- Both spec files are git-ignored (vendor material, not ours to publish); get the PDF from Marstek and regenerate the .md with the `pdf-parse` skill.
- Text version: `docs/MarstekDeviceOpenApi.md`. Grep this file instead of re-parsing the PDF. To regenerate it, use the `pdf-parse` skill.
- Transport: JSON-RPC over **UDP** on the LAN. The port is set in the Marstek app (default 30000). Find devices by broadcasting `Marstek.GetDevice`.
- Local API must be enabled in the Marstek mobile app. Models support different subsets of commands (spec ch. 4).
- Methods: `Marstek.GetDevice`, `Wifi.GetStatus`, `BLE.GetStatus`, `Bat.GetStatus`, `PV.GetStatus`, `ES.GetStatus`, `ES.GetMode`, `ES.SetMode`, `EM.GetStatus`, `DOD.SET`, `Ble.Adv`, `Led.Ctrl`, `Set.Ver`, `Reset.Factory`.
- The doc uses method cards. Every card starts with `<!-- method: name=X access=read|write -->`, and every JSON example has a `<!-- example: method=X kind=request|response -->` marker before it. Split or grep on these markers.
- Errors use JSON-RPC codes (-32700 … -32603, -32000..-32099 server errors).

## Planned layout
- `backend/`: Django project. Apps: `devices` (Marstek UDP client + control endpoints), `stats` (polling and history), `assistant` (AI chat).
- `frontend/`: Vite React app.
- `.claude/`: `settings.json` (hooks), `agents/` (subagents), `skills/` (e.g. `pdf-parse`).
- `docker-compose.yml`, `.env.example`

## Commands
- PDF tooling: `python3 -m venv .venv && .venv/bin/pip install pypdf`
- BE / FE install, run, test, lint, docker build: TBD once scaffolded.
- Git hooks (secret scan via gitleaks, blocks `.env`): `uv tool install pre-commit && pre-commit install`; check all files with `pre-commit run --all-files`.

## Conventions
- Secrets (`ANTHROPIC_API_KEY`, `MARSTEK_HOST`, `MARSTEK_PORT`) go in a git-ignored `.env`. Keep `.env.example` up to date.
- Keep the Marstek UDP client in one module (like an Angular service injected via DI), so views and the AI tools can mock it in tests.
- Write commands (`ES.SetMode`, `DOD.SET`, `Ble.Adv`, `Led.Ctrl`, `Set.Ver`, `Reset.Factory`) change real hardware. Validate their input and never call them from tests.
- `Reset.Factory` is a factory reset. Never expose it to the AI assistant's tools, and require explicit user confirmation anywhere else.
