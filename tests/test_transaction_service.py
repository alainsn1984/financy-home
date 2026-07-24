import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_maker
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.transaction_service import TransactionService


@pytest.fixture(autouse=True)
async def _clean_transactions() -> AsyncGenerator[None, None]:
    async with async_session_maker() as s:
        await s.execute(delete(Transaction))
        await s.commit()
    yield


def _create_data(**overrides: object) -> TransactionCreate:
    defaults: dict[str, object] = dict(
        amount=Decimal("15.75"),
        currency="EUR",
        category="transport",
        description="taxi to airport",
        merchant="Cabify",
        occurred_at=datetime(2026, 7, 18, 14, 30, tzinfo=UTC),
        source_channel="text",
        raw_input="gasté 15.75 en taxi",
        receipt_ref=None,
    )
    defaults.update(overrides)
    return TransactionCreate(**defaults)


async def test_create(session: AsyncSession) -> None:
    service = TransactionService(session)

    tx = await service.create(_create_data())

    assert tx.id is not None
    assert tx.amount == Decimal("15.75")
    assert tx.category == "transport"
    assert tx.source_channel == "text"


async def test_get(session: AsyncSession) -> None:
    service = TransactionService(session)
    created = await service.create(_create_data())

    fetched = await service.get(created.id)

    assert fetched is not None
    assert fetched.id == created.id


async def test_get_unknown_returns_none(session: AsyncSession) -> None:
    service = TransactionService(session)

    fetched = await service.get(uuid.uuid4())

    assert fetched is None


async def test_list_with_filters(session: AsyncSession) -> None:
    service = TransactionService(session)
    await service.create(_create_data(category="transport", source_channel="text"))
    await service.create(_create_data(category="food", source_channel="voice"))
    await service.create(_create_data(category="transport", source_channel="voice"))

    all_txs = await service.list()
    assert len(all_txs) == 3

    by_category = await service.list(category="transport")
    assert len(by_category) == 2
    assert all(tx.category == "transport" for tx in by_category)

    by_channel = await service.list(source_channel="voice")
    assert len(by_channel) == 2
    assert all(tx.source_channel == "voice" for tx in by_channel)

    by_both = await service.list(category="transport", source_channel="voice")
    assert len(by_both) == 1


async def test_list_pagination(session: AsyncSession) -> None:
    service = TransactionService(session)
    for _ in range(3):
        await service.create(_create_data())

    page = await service.list(limit=2, offset=0)
    assert len(page) == 2

    rest = await service.list(limit=2, offset=2)
    assert len(rest) == 1


async def test_update_partial(session: AsyncSession) -> None:
    service = TransactionService(session)
    created = await service.create(_create_data())

    updated = await service.update(created.id, TransactionUpdate(description="updated"))

    assert updated is not None
    assert updated.description == "updated"
    assert updated.amount == Decimal("15.75")
    assert updated.category == "transport"


async def test_update_unknown_returns_none(session: AsyncSession) -> None:
    service = TransactionService(session)

    updated = await service.update(uuid.uuid4(), TransactionUpdate(description="x"))

    assert updated is None


async def test_delete(session: AsyncSession) -> None:
    service = TransactionService(session)
    created = await service.create(_create_data())

    deleted = await service.delete(created.id)
    assert deleted is True

    fetched = await service.get(created.id)
    assert fetched is None


async def test_delete_unknown_returns_false(session: AsyncSession) -> None:
    service = TransactionService(session)

    deleted = await service.delete(uuid.uuid4())

    assert deleted is False
