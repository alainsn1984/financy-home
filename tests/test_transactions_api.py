import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.db import async_session_maker, engine
from app.main import create_app
from app.models.transaction import Transaction


@pytest.fixture(autouse=True)
async def _clean_transactions() -> AsyncGenerator[None, None]:
    async with async_session_maker() as s:
        await s.execute(delete(Transaction))
        await s.commit()
    yield
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _create_payload(**overrides: object) -> dict:
    payload: dict[str, object] = dict(
        amount="15.75",
        currency="EUR",
        category="transport",
        description="taxi to airport",
        merchant="Cabify",
        occurred_at="2026-07-18T14:30:00Z",
        source_channel="text",
        raw_input="gasté 15.75 en taxi",
        receipt_ref=None,
    )
    payload.update(overrides)
    return payload


async def test_crud_happy_path(client: AsyncClient) -> None:
    create_response = await client.post("/api/v1/transactions", json=_create_payload())
    assert create_response.status_code == 201
    created = create_response.json()
    tx_id = created["id"]
    assert created["amount"] == "15.75"
    assert created["category"] == "transport"

    get_response = await client.get(f"/api/v1/transactions/{tx_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == tx_id

    list_response = await client.get("/api/v1/transactions")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = await client.patch(
        f"/api/v1/transactions/{tx_id}", json={"description": "updated"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "updated"
    assert update_response.json()["amount"] == "15.75"

    delete_response = await client.delete(f"/api/v1/transactions/{tx_id}")
    assert delete_response.status_code == 204

    get_after_delete = await client.get(f"/api/v1/transactions/{tx_id}")
    assert get_after_delete.status_code == 404


async def test_list_filters(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/transactions",
        json=_create_payload(category="transport", source_channel="text"),
    )
    await client.post(
        "/api/v1/transactions",
        json=_create_payload(category="food", source_channel="voice"),
    )

    response = await client.get("/api/v1/transactions", params={"category": "food"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["category"] == "food"


async def test_get_unknown_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/transactions/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_update_unknown_returns_404(client: AsyncClient) -> None:
    response = await client.patch(f"/api/v1/transactions/{uuid.uuid4()}", json={"description": "x"})
    assert response.status_code == 404


async def test_delete_unknown_returns_404(client: AsyncClient) -> None:
    response = await client.delete(f"/api/v1/transactions/{uuid.uuid4()}")
    assert response.status_code == 404
