import asyncio
from decimal import Decimal
from uuid import UUID, uuid4

from payments.shared.enums import Currency, PaymentStatus
from payments.webhook.client import WebhookClient
from payments.webhook.services import WebhookDlqPublisher, WebhookNotificationService


class AlwaysFailClient(WebhookClient):
    def __init__(self) -> None:
        self.calls = 0

    async def post(self, url: str, payload: dict[str, object]) -> None:
        self.calls += 1
        raise RuntimeError("network down")


class FailsOnceClient(WebhookClient):
    def __init__(self) -> None:
        self.calls = 0

    async def post(self, url: str, payload: dict[str, object]) -> None:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary failure")


class DummyDlqPublisher(WebhookDlqPublisher):
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    async def publish(self, payload: dict[str, object]) -> None:
        self.messages.append(payload)


def _run(coro):
    return asyncio.run(coro)


def test_webhook_retries_and_sends_to_dlq_after_exhaustion() -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    client = AlwaysFailClient()
    dlq = DummyDlqPublisher()
    service = WebhookNotificationService(
        client=client,
        dlq_publisher=dlq,
        sleep_func=fake_sleep,
        max_attempts=3,
    )

    success = _run(
        service.notify(
            payment_id=uuid4(),
            webhook_url="https://example.com/webhook",
            status=PaymentStatus.FAILED,
            amount=Decimal("10.00"),
            currency=Currency.USD,
            error="gateway_error",
        )
    )

    assert success is False
    assert client.calls == 3
    assert sleep_calls == [1.0, 2.0]
    assert len(dlq.messages) == 1
    assert dlq.messages[0]["queue"] == "payments.dlq"


def test_webhook_stops_retry_after_success() -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    client = FailsOnceClient()
    dlq = DummyDlqPublisher()
    service = WebhookNotificationService(
        client=client,
        dlq_publisher=dlq,
        sleep_func=fake_sleep,
        max_attempts=3,
    )

    success = _run(
        service.notify(
            payment_id=UUID("11111111-1111-1111-1111-111111111111"),
            webhook_url="https://example.com/webhook",
            status=PaymentStatus.SUCCEEDED,
            amount=Decimal("99.00"),
            currency=Currency.EUR,
            error=None,
        )
    )

    assert success is True
    assert client.calls == 2
    assert sleep_calls == [1.0]
    assert dlq.messages == []
