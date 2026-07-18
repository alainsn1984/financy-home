from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Transaction


async def test_transaction_round_trips(session: AsyncSession) -> None:
    occurred = datetime(2026, 7, 18, 14, 30, tzinfo=UTC)
    tx = Transaction(
        amount=Decimal("15.75"),
        currency="EUR",
        category="transport",
        description="taxi to airport",
        merchant="Cabify",
        occurred_at=occurred,
        source_channel="text",
        raw_input="gasté 15.75 en taxi",
        receipt_ref=None,
    )

    session.add(tx)
    await session.commit()
    tx_id = tx.id
    session.expunge_all()

    fetched = (
        await session.execute(select(Transaction).where(Transaction.id == tx_id))
    ).scalar_one()

    assert fetched.id == tx_id
    assert fetched.amount == Decimal("15.75")
    assert isinstance(fetched.amount, Decimal)
    assert fetched.currency == "EUR"
    assert fetched.category == "transport"
    assert fetched.description == "taxi to airport"
    assert fetched.merchant == "Cabify"
    assert fetched.occurred_at == occurred
    assert fetched.occurred_at.tzinfo is not None
    assert fetched.source_channel == "text"
    assert fetched.raw_input == "gasté 15.75 en taxi"
    assert fetched.receipt_ref is None
    assert fetched.created_at.tzinfo is not None
