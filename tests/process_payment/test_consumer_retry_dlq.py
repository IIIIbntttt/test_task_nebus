import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient

from payments.process_payment.consumer import ProcessPaymentConsumer
from payments.process_payment.schemas import PaymentNewMessage


class FailingService:
    async def process_message(self, session, message: PaymentNewMessage) -> None:
        raise RuntimeError("boom")


class DummyPublisher:
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    async def publish(self, queue: str, payload: dict[str, object]) -> None:
        self.messages.append({"queue": queue, "payload": payload})


def _run(coro):
    return asyncio.run(coro)


def test_consumer_requeues_message_before_max_attempts(client: TestClient) -> None:
    publisher = DummyPublisher()
    consumer = ProcessPaymentConsumer(
        service=FailingService(),
        retry_publisher=publisher,
        max_attempts=3,
    )
    payment_id = uuid4()

    _run(consumer.handle(PaymentNewMessage(payment_id=payment_id, attempt=0)))

    assert len(publisher.messages) == 1
    message = publisher.messages[0]
    assert message["queue"] == "payments.new"
    assert message["payload"]["payment_id"] == str(payment_id)
    assert message["payload"]["attempt"] == 1


def test_consumer_sends_to_dlq_after_max_attempts(client: TestClient) -> None:
    publisher = DummyPublisher()
    consumer = ProcessPaymentConsumer(
        service=FailingService(),
        retry_publisher=publisher,
        max_attempts=3,
    )
    payment_id = uuid4()

    _run(consumer.handle(PaymentNewMessage(payment_id=payment_id, attempt=2)))

    assert len(publisher.messages) == 1
    message = publisher.messages[0]
    assert message["queue"] == "payments.dlq"
    assert message["payload"]["payment_id"] == str(payment_id)
    assert message["payload"]["attempt"] == 3
    assert message["payload"]["error"] == "boom"
