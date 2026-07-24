import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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
    model_config = ConfigDict(from_attributes=True)

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
