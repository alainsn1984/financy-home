# SPEC 01 — FastAPI backend scaffolding

> **Status:** Implemented
> **Depends on:** —
> **Date:** 2026-07-18
> **Objective:** Create the runnable FastAPI backend skeleton (layered layout, config, tooling, healthcheck) with no business logic yet.

## Scope

**In:**

- `uv` project init: `pyproject.toml`, pinned Python 3.12, dependency groups (runtime + dev).
- Layered source layout under `app/`: `api/`, `services/`, `models/`, `schemas/`, `core/`.
- App factory (`create_app()`) with versioned router mounted at `/api/v1`.
- Settings via `pydantic-settings` reading `.env`, plus committed `.env.example`.
- Healthcheck endpoint `GET /api/v1/health` returning service status.
- `ruff` config (lint + format) in `pyproject.toml`.
- Minimal `pytest` test asserting healthcheck returns 200.
- `README` note on how to install deps and run the server.

**Out of scope (for future specs):**

- Database layer (SQLAlchemy, Alembic, Postgres connection) — separate spec.
- Docker / docker-compose / infra — separate spec.
- Any of the 3 processing channels (text, voice, vision) — separate specs.
- Messaging integrations (WhatsApp, Telegram bots).
- Auth / users.
- i18n of user-facing content.
- CI pipeline.

## Data model

This spec introduces no domain/persistence structures (those land with the DB spec).

Two config/contract shapes appear:

```python
# app/core/config.py — settings loaded from .env via pydantic-settings
class Settings(BaseSettings):
    app_name: str = "financiera-hogar"
    environment: str = "development"   # development | production
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    # DB / secrets fields added in the DB spec
```

```python
# app/schemas/health.py — healthcheck response contract
class HealthResponse(BaseModel):
    status: str        # "ok"
    service: str       # settings.app_name
    version: str       # app version from pyproject
```

Conventions:

- All code (names, comments, commits) in English.
- Settings are the single source of config; no `os.getenv` scattered in code.

## Implementation plan

1. Init `uv` project: `pyproject.toml` with Python 3.12 pin, `fastapi` + `uvicorn` runtime deps, `ruff` + `pytest` + `httpx` dev deps. Run `uv sync`. Commit.
2. Add `ruff` config (lint + format rules, line length, target 3.12) to `pyproject.toml`. Run `uv run ruff check .` clean on empty tree. Commit.
3. Create `app/core/config.py` with `Settings` + cached `get_settings()`. Add `.env.example` and gitignored `.env`. Commit.
4. Create `app/schemas/health.py` with `HealthResponse`. Commit.
5. Create `app/api/v1/health.py` with `GET /health` router returning `HealthResponse`. Commit.
6. Create `app/api/v1/router.py` aggregating v1 routers; include health router. Commit.
7. Create `app/main.py` with `create_app()` factory: instantiate FastAPI, mount v1 router at `settings.api_v1_prefix`. Run `uv run uvicorn app.main:app`, hit `/api/v1/health`, see `{"status":"ok",...}`. Commit.
8. Add empty-package placeholders `app/services/__init__.py`, `app/models/__init__.py` so the layered layout exists. Commit.
9. Create `tests/test_health.py`: `httpx` client hits `/api/v1/health`, assert 200 + body. Run `uv run pytest`, green. Commit.
10. Update `README` with install (`uv sync`) and run (`uv run uvicorn app.main:app --reload`) instructions. Commit.

## Acceptance criteria

- [ ] `uv sync` installs deps with no errors on a clean checkout.
- [ ] Python is pinned to 3.12 in `pyproject.toml`.
- [ ] `uv run uvicorn app.main:app` starts the server with no errors.
- [ ] `GET /api/v1/health` returns 200 with body `{"status":"ok","service":"financiera-hogar","version":<str>}`.
- [ ] The app is built through a `create_app()` factory, not a module-level global.
- [ ] Config is read only via `Settings`/`get_settings()`; no `os.getenv` calls elsewhere.
- [ ] `.env.example` is committed; `.env` is gitignored.
- [ ] `app/` contains `api/`, `services/`, `models/`, `schemas/`, `core/` directories.
- [ ] `uv run ruff check .` passes with no findings.
- [ ] `uv run ruff format --check .` reports no changes needed.
- [ ] `uv run pytest` passes with the healthcheck test green.
- [ ] `README` documents install and run commands.

## Decisions

- **Yes:** `uv` as package/env manager. Fast, single tool for lock + venv + run.
- **No:** poetry / pip+requirements. More moving parts, slower resolves.
- **Yes:** Python 3.12 pinned. Stable, broad lib support; avoid bleeding-edge 3.13 surprises.
- **Yes:** layered layout (`api/services/models/schemas/core`). Standard FastAPI, clear seams for the DB and channel specs to slot into.
- **No:** feature/module layout (`channels/*` self-contained). Premature; channels don't exist yet, layers scale fine at this size.
- **Yes:** `create_app()` factory. Enables test clients and multiple configs without import-time side effects.
- **Yes:** `/api/v1` prefix from day one. Cheap now, painful to retrofit later.
- **Yes:** `pydantic-settings` + `.env`. Typed config, one source of truth.
- **Yes:** `ruff` for lint + format. One tool replaces flake8 + black + isort.
- **Yes:** ship a healthcheck test now. Locks the app-factory + router wiring so later specs build on a verified base.
- **No:** DB, Docker, channels, auth in this spec. Each is its own spec to keep steps commitable and scope tight.

## Risks

| Risk | Mitigation |
| ---- | ---------- |
| `uv` not installed on the machine | README documents install (`curl -LsSf https://astral.sh/uv/install.sh`); it's a one-time setup step. |
| Layered layout later fights per-channel needs | Layout is additive; a `channels/` package can be introduced by its own spec without moving `core`. |
| Config drift between `.env.example` and real `Settings` | Every new setting must land in both `Settings` and `.env.example`; enforced at review. |

## What is **not** in this spec

- Database layer (SQLAlchemy, Alembic, Postgres) — separate spec.
- Docker / docker-compose / infra — separate spec.
- Processing channels (text, voice, vision) — separate specs.
- Messaging bots (WhatsApp, Telegram).
- Auth / users.
- i18n of user-facing content.
- CI pipeline.

Each one, if it lands, goes in its own spec.
