from faststream import FastStream
from faststream.rabbit import RabbitBroker

from payments.process_payment.consumer import ProcessPaymentConsumer
from payments.process_payment.schemas import PaymentNewMessage
from payments.process_payment.services import ProcessPaymentService
from payments.shared.config import get_settings
from payments.webhook.client import HttpxWebhookClient
from payments.webhook.services import WebhookDlqPublisher, WebhookNotificationService


class RabbitWebhookDlqPublisher(WebhookDlqPublisher):
    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    async def publish(self, payload: dict[str, object]) -> None:
        await self._broker.publish(payload, queue="payments.dlq")


class RabbitRetryPublisher:
    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    async def publish(self, queue: str, payload: dict[str, object]) -> None:
        await self._broker.publish(payload, queue=queue)


settings = get_settings()
broker = RabbitBroker(settings.rabbitmq_url)
dlq_publisher = RabbitWebhookDlqPublisher(broker=broker)
webhook_service = WebhookNotificationService(
    client=HttpxWebhookClient(),
    dlq_publisher=dlq_publisher,
)
process_service = ProcessPaymentService(webhook_service=webhook_service)
retry_publisher = RabbitRetryPublisher(broker=broker)
consumer = ProcessPaymentConsumer(
    service=process_service,
    retry_publisher=retry_publisher,
    max_attempts=3,
)


@broker.subscriber("payments.new")
async def handle_new_payment(message: PaymentNewMessage) -> None:
    await consumer.handle(message)


app = FastStream(broker)
