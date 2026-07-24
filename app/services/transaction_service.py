import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: TransactionCreate) -> Transaction:
        transaction = Transaction(**data.model_dump())
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def get(self, id: uuid.UUID) -> Transaction | None:
        return await self.session.get(Transaction, id)

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        category: str | None = None,
        source_channel: str | None = None,
    ) -> list[Transaction]:
        statement = select(Transaction).offset(offset).limit(limit)
        if category is not None:
            statement = statement.where(Transaction.category == category)
        if source_channel is not None:
            statement = statement.where(Transaction.source_channel == source_channel)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(self, id: uuid.UUID, data: TransactionUpdate) -> Transaction | None:
        transaction = await self.get(id)
        if transaction is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def delete(self, id: uuid.UUID) -> bool:
        transaction = await self.get(id)
        if transaction is None:
            return False
        await self.session.delete(transaction)
        await self.session.commit()
        return True
