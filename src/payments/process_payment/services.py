import asyncio
import random
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from payments.process_payment.repository import ProcessPaymentRepository
from payments.process_payment.schemas import PaymentNewMessage
from payments.shared.enums import PaymentStatus
from payments.webhook.services import WebhookNotificationService, get_webhook_notification_service

RandomProvider = Callable[[], float]
DelayProvider = Callable[[], float]
SleepFunction = Callable[[float], Awaitable[None]]


class ProcessPaymentService:
    def __init__(
        self,
        repository: ProcessPaymentRepository | None = None,
        random_provider: RandomProvider | None = None,
        delay_provider: DelayProvider | None = None,
        sleep_func: SleepFunction = asyncio.sleep,
        webhook_service: WebhookNotificationService | None = None,
    ) -> None:
        self._repository = repository or ProcessPaymentRepository()
        self._random_provider = random_provider or random.random
        self._delay_provider = delay_provider or (lambda: random.uniform(2.0, 5.0))
        self._sleep_func = sleep_func
        self._webhook_service = webhook_service

    async def process_message(self, session: AsyncSession, message: PaymentNewMessage) -> None:
        payment = await self._repository.get_by_id(session, message.payment_id)
        if payment is None:
            return
        if payment.status is not PaymentStatus.PENDING:
            return

        await self._sleep_func(self._delay_provider())
        is_success = self._random_provider() < 0.9

        status = PaymentStatus.SUCCEEDED if is_success else PaymentStatus.FAILED
        last_error = None if is_success else "gateway_error"
        await self._repository.mark_processed(
            session=session,
            payment=payment,
            status=status,
            last_error=last_error,
        )
        await session.commit()

        if self._webhook_service is not None:
            await self._webhook_service.notify(
                payment_id=payment.id,
                webhook_url=payment.webhook_url,
                status=status,
                amount=payment.amount,
                currency=payment.currency,
                error=last_error,
            )


def get_process_payment_service() -> ProcessPaymentService:
    return ProcessPaymentService(
        repository=ProcessPaymentRepository(),
        webhook_service=get_webhook_notification_service(),
    )
