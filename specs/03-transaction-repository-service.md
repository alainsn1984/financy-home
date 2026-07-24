# SPEC 03 — Transaction repository/service layer

> **Status:** Implemented
> **Depends on:** SPEC 02
> **Date:** 2026-07-24
> **Objective:** Add a service layer over `Transaction` (create/get/list/update/delete) that the 3 future channels and API routes reuse, instead of each caller writing raw SQLModel queries.

## Scope

**In:**

- `app/services/transaction_service.py`: `TransactionService` class wrapping an `AsyncSession`, with methods:
  - `create(data: TransactionCreate) -> Transaction`
  - `get(id: uuid.UUID) -> Transaction | None`
  - `list(*, limit: int = 50, offset: int = 0, category: str | None = None, source_channel: str | None = None) -> list[Transaction]`
  - `update(id: uuid.UUID, data: TransactionUpdate) -> Transaction | None`
  - `delete(id: uuid.UUID) -> bool`
- `app/schemas/transaction.py`: Pydantic request/response schemas (`TransactionCreate`, `TransactionUpdate`, `TransactionRead`) decoupled from the SQLModel table model.
- `get_transaction_service()` FastAPI dependency composing `get_session()` + `TransactionService`.
- Minimal CRUD router `app/api/v1/transactions.py`:
  - `POST /api/v1/transactions`
  - `GET /api/v1/transactions/{id}`
  - `GET /api/v1/transactions` (paginated, filterable by `category`/`source_channel`)
  - `PATCH /api/v1/transactions/{id}`
  - `DELETE /api/v1/transactions/{id}`
- `tests/test_transaction_service.py`: service-level tests against real Postgres (reuse SPEC 02 fixture).
- `tests/test_transactions_api.py`: HTTP-level tests for the router (happy path + 404s).

**Out of scope (for future specs):**

- Categorization / NLP parsing logic — channel specs call `TransactionService.create` with already-parsed data.
- Text/voice/vision channels themselves.
- User/member model, auth, ownership checks, FK on `Transaction`.
- Business rules: savings goals, budget-deviation alerts, aggregated history/reporting endpoints.
- Cursor-based pagination (offset/limit is enough for now).
- Soft-delete / audit trail on `Transaction`.

## Data model

No changes to the `Transaction` table (SPEC 02). New Pydantic-only shapes:

```python
# app/schemas/transaction.py
class TransactionCreate(BaseModel):
    amount: Decimal
    currency: str = "EUR"
    category: str | None = None
    description: str | None = None
    merchant: str | None = None
    occurred_at: datetime
    source_channel: str
    raw_input: str | None = None
    receipt_ref: str | None = None

class TransactionUpdate(BaseModel):
    amount: Decimal | None = None
    currency: str | None = None
    category: str | None = None
    description: str | None = None
    merchant: str | None = None
    occurred_at: datetime | None = None
    receipt_ref: str | None = None

class TransactionRead(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    category: str | None
    description: str | None
    merchant: str | None
    occurred_at: datetime
    source_channel: str
    raw_input: str | None
    receipt_ref: str | None
    created_at: datetime
```

Conventions:

- Schemas live in `app/schemas/`, table model stays in `app/models/`; router/service never leak the SQLModel table type past the service boundary in responses (`TransactionRead` is the contract).
- `TransactionUpdate` fields all optional; service applies only fields set (`exclude_unset=True`), no accidental overwrites with `None`.
- `source_channel` is not updatable (set once at creation, matches the channel that wrote it).
- Service methods raise nothing on not-found; return `None`/`False` and let the router translate to HTTP 404.

## Implementation plan

1. Create `app/schemas/transaction.py` with `TransactionCreate`, `TransactionUpdate`, `TransactionRead`. Commit.
2. Create `app/services/transaction_service.py` with `TransactionService(session: AsyncSession)` and `create`/`get`/`list`/`update`/`delete`. Commit.
3. Add `get_transaction_service()` dependency (in `app/services/transaction_service.py` or `app/core/dependencies.py`) yielding `TransactionService` built from `get_session()`. Commit.
4. Add `tests/test_transaction_service.py`: create, get, list with filters, update (partial), delete, get-after-delete returns `None`. Run against real Postgres via existing conftest fixture. Commit.
5. Create `app/api/v1/transactions.py` with the 5 routes, using `TransactionRead` as response model and `get_transaction_service` as dependency. Commit.
6. Wire `transactions` router into `app/api/v1/router.py`. Commit.
7. Add `tests/test_transactions_api.py`: `httpx` client covers create→get→list→update→delete happy path, plus 404 on unknown id. Run `uv run pytest`, green. Commit.
8. Update `README` with a short note on the transactions CRUD endpoints. Commit.

## Acceptance criteria

- [x] `TransactionService` exposes `create`/`get`/`list`/`update`/`delete`; no raw SQLModel/session calls in the router.
- [x] `list` supports `limit`/`offset` and optional `category`/`source_channel` filters.
- [x] `update` applies only explicitly-set fields (partial update semantics).
- [x] `TransactionCreate`/`TransactionUpdate`/`TransactionRead` fully decouple the API contract from the `Transaction` table model.
- [x] `POST/GET/GET-list/PATCH/DELETE /api/v1/transactions[/{id}]` all work end-to-end against real Postgres.
- [x] Unknown `id` on get/update/delete returns 404, not a 500 or silent no-op.
- [x] `uv run pytest` passes: service tests + API tests, both against real Postgres.
- [x] `uv run ruff check .` and `uv run ruff format --check .` pass.
- [x] `README` documents the transactions endpoints.

## Decisions

- **Yes:** service layer between router and SQLModel. Channels (text/voice/vision) and the API both call the same `TransactionService`, no duplicated query logic.
- **No:** repository pattern with abstract interface/multiple backends. One Postgres backend, no swapping planned; the interface would be pure ceremony.
- **Yes:** separate Pydantic schemas (`TransactionCreate`/`Update`/`Read`) instead of reusing the SQLModel table class in the API. Keeps DB shape free to evolve without breaking the API contract, and vice versa.
- **Yes:** partial update via `exclude_unset=True`. Standard PATCH semantics; avoids clobbering fields the caller didn't mention.
- **No:** `source_channel` in `TransactionUpdate`. It's provenance, set once at write time by whichever channel created the record.
- **Yes:** offset/limit pagination. Simplest thing that works at current scale (single family, low volume); cursor pagination is premature.
- **No:** categorization/NLP in this spec. That's the text-channel spec; this layer only persists whatever category it's given.
- **Yes:** CRUD router included now, even though no channel writes through it yet. Gives a concrete, testable consumer of the service and an early manual-testing path (`curl`/OpenAPI docs) before channels exist.

## Risks

| Risk | Mitigation |
| ---- | ---------- |
| Service becomes a thin pass-through with no real value | Partial-update logic and filtered listing already justify it; channel specs will add categorization calls through the same seam. |
| API schema drifts from table model as fields get added later | Both live under `app/schemas/` and `app/models/`; any new `Transaction` field must be added to `TransactionRead` (and `Create`/`Update` if writable) in the same PR. |
| PATCH with all-`None` body silently no-ops | `exclude_unset=True` (not `exclude_none`) so an explicit `null` still applies; an empty body applies nothing — acceptable, documented in the endpoint. |
| Pagination defaults let a caller pull unbounded rows | `limit` capped server-side (e.g. max 200) regardless of requested value. |

## What is **not** in this spec

- Categorization/NLP parsing — channel specs.
- Text/voice/vision channels — separate specs.
- User/member model, auth, ownership — auth spec.
- Savings goals, budget alerts, reporting/aggregation endpoints — business-logic specs.
- Cursor pagination, soft delete — future, if ever needed.

Each one, if it lands, goes in its own spec.
