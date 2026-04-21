from typing import Protocol

from payments.process_payment.schemas import PaymentNewMessage
from payments.process_payment.services import ProcessPaymentService
from payments.shared.db import get_session_factory


class RetryPublisher(Protocol):
    async def publish(self, queue: str, payload: dict[str, object]) -> None:
        ...


class ProcessPaymentConsumer:
    def __init__(
        self,
        service: ProcessPaymentService,
        retry_publisher: RetryPublisher | None = None,
        max_attempts: int = 3,
    ) -> None:
        self._service = service
        self._retry_publisher = retry_publisher
        self._max_attempts = max_attempts

    async def handle(self, payload: PaymentNewMessage) -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                await self._service.process_message(session, payload)
            except Exception as exc:  # noqa: BLE001
                if self._retry_publisher is None:
                    raise
                await self._handle_failure(payload, str(exc))

    async def _handle_failure(self, payload: PaymentNewMessage, error: str) -> None:
        publisher = self._retry_publisher
        assert publisher is not None
        next_attempt = payload.attempt + 1
        if next_attempt < self._max_attempts:
            await publisher.publish(
                queue="payments.new",
                payload={"payment_id": str(payload.payment_id), "attempt": next_attempt},
            )
            return

        await publisher.publish(
            queue="payments.dlq",
            payload={
                "payment_id": str(payload.payment_id),
                "attempt": next_attempt,
                "error": error,
            },
        )
