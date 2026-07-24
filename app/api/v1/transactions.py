import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from app.services.transaction_service import TransactionService, get_transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])

MAX_LIMIT = 200


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    transaction = await service.create(data)
    return TransactionRead.model_validate(transaction)


@router.get("/{id}", response_model=TransactionRead)
async def get_transaction(
    id: uuid.UUID,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    transaction = await service.get(id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    limit: int = 50,
    offset: int = 0,
    category: str | None = None,
    source_channel: str | None = None,
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionRead]:
    transactions = await service.list(
        limit=min(limit, MAX_LIMIT),
        offset=offset,
        category=category,
        source_channel=source_channel,
    )
    return [TransactionRead.model_validate(t) for t in transactions]


@router.patch("/{id}", response_model=TransactionRead)
async def update_transaction(
    id: uuid.UUID,
    data: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    transaction = await service.update(id, data)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    id: uuid.UUID,
    service: TransactionService = Depends(get_transaction_service),
) -> None:
    deleted = await service.delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
