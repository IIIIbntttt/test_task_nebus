from sqlalchemy.ext.asyncio import AsyncSession

from payments.outbox.publisher import OutboxEventPublisher
from payments.outbox.repository import OutboxRepository


class OutboxPublisherService:
    def __init__(self, repository: OutboxRepository, publisher: OutboxEventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    async def flush_pending(self, session: AsyncSession) -> int:
        pending_events = await self._repository.get_pending(session)
        published_count = 0

        for event in pending_events:
            await self._publisher.publish(event.event_type, event.payload)
            await self._repository.mark_published(session, event.id)
            published_count += 1

        await session.commit()
        return published_count
