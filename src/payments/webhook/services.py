import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from payments.shared.enums import Currency, PaymentStatus
from payments.webhook.client import HttpxWebhookClient, WebhookClient
from payments.webhook.retry import exponential_backoff_delay_seconds

SleepFunction = Callable[[float], Awaitable[None]]


class WebhookDlqPublisher(Protocol):
    async def publish(self, payload: dict[str, object]) -> None:
        ...


class NullWebhookDlqPublisher:
    async def publish(self, payload: dict[str, object]) -> None:
        return None


class WebhookNotificationService:
    def __init__(
        self,
        client: WebhookClient,
        dlq_publisher: WebhookDlqPublisher,
        sleep_func: SleepFunction = asyncio.sleep,
        max_attempts: int = 3,
    ) -> None:
        self._client = client
        self._dlq_publisher = dlq_publisher
        self._sleep_func = sleep_func
        self._max_attempts = max_attempts

    async def notify(
        self,
        payment_id: UUID,
        webhook_url: str,
        status: PaymentStatus,
        amount: Decimal,
        currency: Currency,
        error: str | None,
    ) -> bool:
        payload: dict[str, object] = {
            "payment_id": str(payment_id),
            "status": status.value,
            "amount": str(amount),
            "currency": currency.value,
            "error": error,
        }

        for attempt_index in range(self._max_attempts):
            try:
                await self._client.post(webhook_url, payload)
                return True
            except Exception as exc:  # noqa: BLE001
                if attempt_index == self._max_attempts - 1:
                    await self._dlq_publisher.publish(
                        {
                            "queue": "payments.dlq",
                            "payload": payload,
                            "webhook_url": webhook_url,
                            "error": str(exc),
                        }
                    )
                    return False

                delay = exponential_backoff_delay_seconds(attempt_index)
                await self._sleep_func(delay)

        return False


def get_webhook_notification_service() -> WebhookNotificationService:
    return WebhookNotificationService(
        client=HttpxWebhookClient(),
        dlq_publisher=NullWebhookDlqPublisher(),
    )
