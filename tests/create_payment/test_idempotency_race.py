import asyncio
from decimal import Decimal

from sqlalchemy import select

from payments.create_payment.repository import CreatePaymentRepository
from payments.create_payment.schemas import CreatePaymentRequest
from payments.shared.db import get_session_factory
from payments.shared.models import OutboxModel


def _run(coro):
    return asyncio.run(coro)


def test_create_with_outbox_handles_duplicate_idempotency_key_without_500(client) -> None:
    repository = CreatePaymentRepository()
    payload = CreatePaymentRequest(
        amount=Decimal("100.00"),
        currency="USD",
        description="first",
        metadata={},
        webhook_url="https://example.com/webhook",
    )
    idempotency_key = "race-idem-key"

    first_payment = _run(_create(repository, payload, idempotency_key))

    second_payload = CreatePaymentRequest(
        amount=Decimal("999.00"),
        currency="USD",
        description="second",
        metadata={"changed": True},
        webhook_url="https://example.com/webhook-2",
    )
    second_payment = _run(_create(repository, second_payload, idempotency_key))

    assert first_payment.id == second_payment.id
    outbox_count = _run(_outbox_count())
    assert outbox_count == 1


async def _create(
    repository: CreatePaymentRepository,
    payload: CreatePaymentRequest,
    idempotency_key: str,
):
    session_factory = get_session_factory()
    async with session_factory() as session:
        return await repository.create_with_outbox(session, payload, idempotency_key)


async def _outbox_count() -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(OutboxModel.id))
        return len(list(result))
