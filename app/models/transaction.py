import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class Transaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    currency: str = Field(default="EUR", max_length=3)
    category: str | None = None
    description: str | None = None
    merchant: str | None = None
    occurred_at: datetime
    source_channel: str
    raw_input: str | None = None
    receipt_ref: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
