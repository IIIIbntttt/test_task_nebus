import asyncio
import logging
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from payments.outbox.publisher import OutboxEventPublisher
from payments.outbox.repository import OutboxRepository
from payments.outbox.services import OutboxPublisherService
from payments.shared.db import get_session_factory

logger = logging.getLogger(__name__)


class OutboxFlusher(Protocol):
    async def flush_pending(self, session: AsyncSession) -> int:
        ...


async def run_outbox_iteration(
    service: OutboxFlusher,
    session_factory: async_sessionmaker[AsyncSession],
) -> bool:
    try:
        async with session_factory() as session:
            await service.flush_pending(session)
    except Exception:  # noqa: BLE001
        logger.exception("Outbox iteration failed")
        return False
    return True


async def run_outbox_worker(publisher: OutboxEventPublisher, interval_seconds: float = 1.0) -> None:
    repository = OutboxRepository()
    service = OutboxPublisherService(repository=repository, publisher=publisher)
    session_factory = get_session_factory()

    while True:
        await run_outbox_iteration(service, session_factory)
        await asyncio.sleep(interval_seconds)
