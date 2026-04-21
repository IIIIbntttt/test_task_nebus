import asyncio
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select

from payments.process_payment.schemas import PaymentNewMessage
from payments.process_payment.services import ProcessPaymentService
from payments.shared.db import get_session_factory
from payments.shared.enums import PaymentStatus
from payments.shared.models import PaymentModel
from payments.webhook.services import WebhookNotificationService


def _run(coro):
    return asyncio.run(coro)


async def _noop_sleep(_: float) -> None:
    return None


class TrackingWebhookService(WebhookNotificationService):
    def __init__(self) -> None:
        self.calls = 0

    async def notify(
        self,
        payment_id,
        webhook_url: str,
        status: PaymentStatus,
        amount,
        currency,
        error: str | None,
    ) -> bool:
        self.calls += 1
        return True


def test_process_payment_succeeds_when_gateway_returns_success(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key", "Idempotency-Key": "proc-idem-1"},
        json={
            "amount": "30.00",
            "currency": "USD",
            "description": "Process success test",
            "metadata": {},
            "webhook_url": "https://example.com/webhook",
        },
    )
    payment_id = UUID(create_response.json()["payment_id"])

    service = ProcessPaymentService(
        random_provider=lambda: 0.1,
        delay_provider=lambda: 0.0,
        sleep_func=_noop_sleep,
    )
    _run(_process_message(service, payment_id))

    payment = _run(_fetch_payment(payment_id))
    assert payment is not None
    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.processed_at is not None


def test_process_payment_fails_when_gateway_returns_error(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key", "Idempotency-Key": "proc-idem-2"},
        json={
            "amount": "30.00",
            "currency": "USD",
            "description": "Process failure test",
            "metadata": {},
            "webhook_url": "https://example.com/webhook",
        },
    )
    payment_id = UUID(create_response.json()["payment_id"])

    service = ProcessPaymentService(
        random_provider=lambda: 0.95,
        delay_provider=lambda: 0.0,
        sleep_func=_noop_sleep,
    )
    _run(_process_message(service, payment_id))

    payment = _run(_fetch_payment(payment_id))
    assert payment is not None
    assert payment.status == PaymentStatus.FAILED
    assert payment.processed_at is not None


def test_process_payment_is_idempotent_for_already_processed_payment(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key", "Idempotency-Key": "proc-idem-3"},
        json={
            "amount": "30.00",
            "currency": "USD",
            "description": "Process idempotency test",
            "metadata": {},
            "webhook_url": "https://example.com/webhook",
        },
    )
    payment_id = UUID(create_response.json()["payment_id"])
    webhook_service = TrackingWebhookService()

    first = ProcessPaymentService(
        random_provider=lambda: 0.1,
        delay_provider=lambda: 0.0,
        sleep_func=_noop_sleep,
        webhook_service=webhook_service,
    )
    _run(_process_message(first, payment_id))

    payment_after_first = _run(_fetch_payment(payment_id))
    assert payment_after_first is not None
    first_processed_at = payment_after_first.processed_at

    second = ProcessPaymentService(
        random_provider=lambda: 0.95,
        delay_provider=lambda: 0.0,
        sleep_func=_noop_sleep,
        webhook_service=webhook_service,
    )
    _run(_process_message(second, payment_id))

    payment_after_second = _run(_fetch_payment(payment_id))
    assert payment_after_second is not None
    assert payment_after_second.status == PaymentStatus.SUCCEEDED
    assert payment_after_second.processed_at == first_processed_at
    assert webhook_service.calls == 1


async def _process_message(service: ProcessPaymentService, payment_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await service.process_message(session, PaymentNewMessage(payment_id=payment_id))


async def _fetch_payment(payment_id: UUID) -> PaymentModel | None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(PaymentModel).where(PaymentModel.id == payment_id))
        return result.scalar_one_or_none()
