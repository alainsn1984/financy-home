# SPEC 02 — Database layer (SQLModel + Alembic + Postgres)

> **Status:** Implemented
> **Depends on:** SPEC 01
> **Date:** 2026-07-19
> **Objective:** Add the async Postgres persistence layer (SQLModel engine/session, `Transaction` model, Alembic migrations) so the backend can store and read transactions.

## Scope

**In:**

- Runtime deps: `sqlmodel`, `asyncpg`, `alembic`. Added via `uv`.
- `DATABASE_URL` field in `Settings` (async driver, e.g. `postgresql+asyncpg://...`).
- `app/core/db.py`: async engine, `async_sessionmaker`, `get_session()` FastAPI dependency.
- `Transaction` SQLModel table model in `app/models/transaction.py`.
- Alembic setup (`alembic.ini`, async `migrations/env.py`) with autogenerate; initial migration creating the `transaction` table.
- Minimal `docker-compose.yml` with a single Postgres service for dev/test.
- `pytest` DB test: run `alembic upgrade head` against real Postgres, then insert + select a `Transaction`.
- `.env.example` updated with `DATABASE_URL`.
- `README` note: start Postgres (compose), run migrations, run DB tests.

**Out of scope (for future specs):**

- User/member model and FK on `Transaction` (auth spec).
- Business logic: categorization, savings goals, budget alerts.
- The 3 processing channels (text, voice, vision) writing transactions.
- Repository/service layer over the model (channel specs add it).
- DB `SELECT 1` ping in `/api/v1/health` (kept as-is this spec).
- Full app Dockerfile + infra compose (Docker spec).
- Postgres enum types for `category`/`source_channel` — kept as `str`.
- Seed data / fixtures beyond what tests need.

## Data model

```python
# app/models/transaction.py
class Transaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    amount: Decimal = Field(max_digits=12, decimal_places=2)  # importe
    currency: str = Field(default="EUR", max_length=3)        # ISO 4217
    category: str | None = None                               # NLP-classified
    description: str | None = None                            # free text
    merchant: str | None = None                               # from OCR/vision
    occurred_at: datetime                                     # when the expense happened
    source_channel: str                                       # "text" | "voice" | "image"
    raw_input: str | None = None                              # original text / transcription
    receipt_ref: str | None = None                            # path/URL to backup receipt image
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

```python
# app/core/config.py — new field
class Settings(BaseSettings):
    ...
    database_url: str  # e.g. "postgresql+asyncpg://user:pass@localhost:5432/financiera_hogar"
```

Conventions:

- `amount` as `Decimal` (never float) — money precision.
- Timestamps timezone-aware, UTC.
- `source_channel` / `category` are validated in the app/schema layer, not DB enums.
- Table name `transaction` (SQLModel default from class name, lowercased).

## Implementation plan

1. Add deps `sqlmodel`, `asyncpg`, `alembic` via `uv add`. Run `uv sync`. Commit.
2. Add `docker-compose.yml` with one Postgres service (named volume, exposed `5432`, env for user/pass/db). Run `docker compose up -d`, confirm container healthy. Commit.
3. Add `database_url` to `Settings`; add `DATABASE_URL` to `.env.example` and gitignored `.env`. Commit.
4. Create `app/core/db.py`: async engine from `settings.database_url`, `async_sessionmaker`, `async def get_session()` dependency yielding an `AsyncSession`. Commit.
5. Create `app/models/transaction.py` with the `Transaction` model. Import it in `app/models/__init__.py` so metadata sees it. Commit.
6. Init Alembic (`alembic init migrations`); rewrite `migrations/env.py` for async engine + `SQLModel.metadata` as target; point `sqlalchemy.url` at `settings.database_url`. Commit.
7. Autogenerate initial migration (`alembic revision --autogenerate -m "create transaction table"`); review it creates `transaction`. Run `alembic upgrade head`, confirm table exists. Commit.
8. Add `tests/conftest.py`: fixture that runs `alembic upgrade head` (or creates schema) against the test Postgres and provides an `AsyncSession`. Commit.
9. Add `tests/test_db.py`: insert a `Transaction`, select it back, assert fields round-trip. Run `uv run pytest`, green. Commit.
10. Update `README`: start Postgres via compose, `alembic upgrade head`, run tests. Commit.

## Acceptance criteria

- [x] `uv sync` installs `sqlmodel`, `asyncpg`, `alembic` with no errors.
- [x] `docker compose up -d` starts a Postgres container that accepts connections.
- [x] `Settings` exposes `database_url`; `DATABASE_URL` is in `.env.example` and `.env` is gitignored.
- [x] `app/core/db.py` provides an async engine, `async_sessionmaker`, and a `get_session()` dependency yielding `AsyncSession`.
- [x] `Transaction` model exists with all fields from the data model section.
- [x] `alembic upgrade head` creates the `transaction` table on a clean DB with no errors.
- [x] `alembic downgrade base` drops it cleanly (reversible migration).
- [x] The autogenerated migration diff is empty right after `upgrade head` (model matches schema).
- [x] `uv run pytest` passes: inserting a `Transaction` and selecting it back round-trips every field (including `Decimal` amount and UTC timestamps).
- [x] `uv run ruff check .` and `uv run ruff format --check .` pass.
- [x] `README` documents: start Postgres, run migrations, run tests.

## Decisions

- **Yes:** SQLModel over raw SQLAlchemy. One class = table model + Pydantic schema; fits FastAPI, less duplication.
- **Yes:** async stack (`asyncpg` + `AsyncSession` + `create_async_engine`). Matches FastAPI's event loop; no thread-pool for DB I/O.
- **No:** sync `psycopg` + `Session`. Would block the loop and diverge from channel I/O later.
- **Yes:** `Transaction` modeled in this spec. Shared model all 3 channels converge on; needed to make the DB layer real, not abstract.
- **No:** FK to user/member now. Auth is a separate spec; column added when it lands.
- **Yes:** `str` for `category`/`source_channel` + app-layer validation. Postgres enums are painful to migrate.
- **Yes:** `Decimal` for `amount`. Money precision; floats corrupt cents.
- **Yes:** `EUR` default currency. Primary user is euro-based.
- **Yes:** Alembic with autogenerate. Versioned, reversible schema from day one.
- **No:** `SQLModel.metadata.create_all()` as the schema source. Fine for toy apps; Alembic is the real migration path.
- **Yes:** minimal `docker-compose.yml` (Postgres only). Reproducible dev/test DB without hand-installing Postgres.
- **No:** full app Dockerfile / infra compose here. Its own spec.
- **Yes:** tests hit real Postgres. Faithful to prod types/migrations; SQLite would lie.
- **No:** SQLite for tests. Diverges on types, `Decimal`, and migration behavior.

## Risks

| Risk | Mitigation |
| ---- | ---------- |
| Async Alembic `env.py` misconfigured (autogenerate empty or fails) | Step 7 verifies the migration creates `transaction` and a second autogenerate is empty; documented in `migrations/env.py`. |
| Tests need a live Postgres; absent in CI | Compose brings up Postgres; test `DATABASE_URL` points at it. If DB down, DB tests fail loud (not skipped silently). |
| `Decimal`/timezone round-trip drift through `asyncpg` | `test_db.py` asserts exact `amount` and UTC timestamp equality on read-back. |
| Test DB pollution between runs | Fixture runs `alembic upgrade head` on a clean/rolled-back state; migrations reversible (`downgrade base`). |
| Committing real credentials in `.env` | Only `.env.example` committed with placeholders; `.env` gitignored (from SPEC 01). |

## What is **not** in this spec

- User/member model and FK on `Transaction` — auth spec.
- Categorization, savings goals, budget alerts — business-logic specs.
- Text/voice/vision channels writing transactions — channel specs.
- Repository/service layer over the model — channel specs.
- DB ping in `/api/v1/health` — later.
- Full app Dockerfile + infra compose — Docker spec.
- Postgres enum types — kept as `str`.

Each one, if it lands, goes in its own spec.
