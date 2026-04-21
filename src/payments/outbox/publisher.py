from typing import Protocol

from faststream.rabbit import RabbitBroker


class OutboxEventPublisher(Protocol):
    async def publish(self, routing_key: str, payload: dict[str, object]) -> None:
        ...


class RabbitOutboxPublisher:
    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    async def publish(self, routing_key: str, payload: dict[str, object]) -> None:
        await self._broker.publish(payload, queue=routing_key)
