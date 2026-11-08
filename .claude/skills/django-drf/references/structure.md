# Structure, settings, tooling

```
backend/
├── pyproject.toml          # deps + ruff/mypy/pytest config (uv-managed)
├── manage.py
├── config/                 # Django project (settings, root urls, asgi/wsgi)
│   ├── settings.py
│   └── urls.py             # path("api/", include(...)) per app
├── devices/
│   ├── marstek/            # client.py, types.py, exceptions.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
├── stats/                  # models.py (readings), services.py, management/commands/poll_device.py
└── assistant/              # tools.py (tool schemas + handlers), services.py (Anthropic loop), views.py
```
- One app per domain. Apps import each other's **services**, not views.
- Keep `tests/` as a package per app (`test_views.py`, `test_services.py`).

## Settings
```python
import environ  # django-environ
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR.parent / ".env")
SECRET_KEY = env("SECRET_KEY")
MARSTEK_HOST = env("MARSTEK_HOST", default="")
MARSTEK_PORT = env.int("MARSTEK_PORT", default=30000)
MARSTEK_TIMEOUT = env.float("MARSTEK_TIMEOUT", default=2.0)
REST_FRAMEWORK = {"EXCEPTION_HANDLER": "devices.exceptions.api_exception_handler"}
```
Read settings through `django.conf.settings`, never `os.environ` scattered in modules.

## Commands (explain `uv` the first time: it's like npm + nvm for Python)
- `uv sync` — install deps into `.venv` (like `npm ci`)
- `uv run python manage.py runserver` / `migrate` / `makemigrations`
- `uv run pytest` — tests
- `uv run ruff check . && uv run ruff format .` — lint + format (like ESLint + Prettier)
- `uv run mypy .` — type check (with `django-stubs`, `djangorestframework-stubs`)

## Polling (stats)
Start simple: a management command `poll_device` that loops with `time.sleep(interval)` and stores
readings; run it as its own docker-compose service. Move to Celery beat only if needed.
