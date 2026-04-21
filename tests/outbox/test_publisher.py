import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from payments.outbox.publisher import OutboxEventPublisher
from payments.outbox.repository import OutboxRepository
from payments.outbox.services import OutboxPublisherService
from payments.shared.db import get_session_factory
from payments.shared.enums import OutboxStatus
from payments.shared.models import OutboxModel


class DummyPublisher(OutboxEventPublisher):
    def __init__(self) -> None:
        self.published: list[dict[str, object]] = []

    async def publish(self, routing_key: str, payload: dict[str, object]) -> None:
        self.published.append({"routing_key": routing_key, "payload": payload})


def _run(coro):
    return asyncio.run(coro)


def test_outbox_publishes_pending_events(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key", "Idempotency-Key": "outbox-idem-1"},
        json={
            "amount": "20.00",
            "currency": "USD",
            "description": "Outbox test",
            "metadata": {"kind": "outbox"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert create_response.status_code == 202

    publisher = DummyPublisher()
    service = OutboxPublisherService(repository=OutboxRepository(), publisher=publisher)
    _run(_flush_once(service))

    assert len(publisher.published) == 1
    assert publisher.published[0]["routing_key"] == "payments.new"

    outbox_rows = _run(_fetch_outbox_rows())
    assert len(outbox_rows) == 1
    assert outbox_rows[0].status == OutboxStatus.PUBLISHED


async def _flush_once(service: OutboxPublisherService) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await service.flush_pending(session)


async def _fetch_outbox_rows() -> list[OutboxModel]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(OutboxModel))
        return list(result.scalars())
