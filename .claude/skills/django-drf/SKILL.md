---
name: django-drf
description: Best practices for writing Python + Django + Django REST Framework code in this project's backend (backend/). Covers app layout, models, serializers, views/viewsets, URL routing, the service layer, the Marstek UDP/JSON-RPC client, settings and .env, polling/history for stats, the AI assistant's tool layer, and testing with pytest + pytest-django. Use this whenever you create, edit, refactor or review any .py file under backend/, add an endpoint/model/serializer/management command, talk to the Marstek device, set up backend tooling (uv, ruff, mypy, pytest), or write backend tests — even if the user doesn't say "best practices" or "Django".
---

# Django + DRF best practices

Stack: Python 3.12+, Django 5.x, Django REST Framework, pytest + pytest-django, ruff, mypy (or pyright),
`uv` for env/deps. Apps: `devices` (UDP client + control endpoints), `stats` (polling + history),
`assistant` (Anthropic tool-use chat). The device API spec lives in `docs/MarstekDeviceOpenApi.md`; grep
its `<!-- method: name=X -->` markers instead of guessing field names.

Read the reference file for the area you're touching:
- `references/structure.md` — project/app layout, settings, .env, tooling commands
- `references/api-layer.md` — models, serializers, views, URLs, errors, the service layer
- `references/marstek-client.md` — UDP JSON-RPC client, DI/mocking, write-command safety
- `references/testing.md` — pytest-django conventions, fixtures, mocking the client

## Core rules (apply always)

1. **Thin views, logic in services.** Views parse/validate (serializer), call one service function,
   return a response. Business logic lives in `services.py`, device I/O in the client. (Angular analogy:
   component → service → HttpClient.)
2. **Serializers are the validation boundary.** Every request body goes through a serializer's
   `is_valid(raise_exception=True)`. Never read `request.data["x"]` raw. Use `ChoiceField` for enums.
3. **One Marstek client module** (`devices/marstek/client.py`). Nothing else opens sockets. Views,
   services, stats polling and AI tools get it via a factory (`get_client()`) so tests can swap it.
4. **Write commands change real hardware.** `ES.SetMode`, `DOD.SET`, `Ble.Adv`, `Led.Ctrl`, `Set.Ver`,
   `Reset.Factory`: validate ranges/choices strictly, log them, use POST only, and never hit a real
   device from tests. `Reset.Factory` requires an explicit confirmation field and is never an AI tool.
5. **Type hints everywhere**, including return types. Use `TypedDict`/dataclasses for device payloads,
   not loose `dict[str, Any]` leaking into views.
6. **Map device failures to HTTP clearly.** Timeout → 504, JSON-RPC error → 502 with the code/message,
   validation → 400. Raise domain exceptions in the client; translate them in one exception handler.
7. **Config from environment.** `MARSTEK_HOST`, `MARSTEK_PORT`, `ANTHROPIC_API_KEY`, `SECRET_KEY` come
   from `.env` via settings; never hardcode, never commit. Update `.env.example` when adding one.
8. **Idiomatic Python.** f-strings, `pathlib`, comprehensions where readable, `logging` not `print`,
   no mutable default args, `snake_case` names. Let `ruff` decide formatting.
9. **ORM care.** Use `select_related`/`prefetch_related` to avoid N+1, index time columns you filter on,
   write migrations with `makemigrations` (never hand-edit applied ones).
10. **Tests ship with the code.** Each endpoint gets an API test with the client mocked.

## When reviewing code
List concrete issues with the rule they break and a fixed snippet. Prioritize: correctness and hardware
safety > security (secrets, validation) > type safety > structure > style.

## Mentor notes
The user knows Angular/TS, not Python. When introducing a Django concept, add one line relating it to
an Angular/TS idea (serializer ≈ typed DTO + validator, `urls.py` ≈ router config, fixture ≈ TestBed provider).
