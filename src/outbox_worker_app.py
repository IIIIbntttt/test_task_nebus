import asyncio

from faststream.rabbit import RabbitBroker

from payments.outbox.publisher import RabbitOutboxPublisher
from payments.outbox.worker import run_outbox_worker
from payments.shared.config import get_settings


async def main() -> None:
    settings = get_settings()
    broker = RabbitBroker(settings.rabbitmq_url)
    await broker.connect()
    publisher = RabbitOutboxPublisher(broker=broker)
    await run_outbox_worker(publisher=publisher)


if __name__ == "__main__":
    asyncio.run(main())
