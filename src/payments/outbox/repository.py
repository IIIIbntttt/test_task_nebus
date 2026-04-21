from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payments.outbox.schemas import OutboxEvent
from payments.shared.enums import OutboxStatus
from payments.shared.models import OutboxModel


class OutboxRepository:
    async def get_pending(self, session: AsyncSession, limit: int = 100) -> list[OutboxEvent]:
        stmt = (
            select(OutboxModel)
            .where(OutboxModel.status == OutboxStatus.PENDING)
            .order_by(OutboxModel.id.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = list(result.scalars())
        return [
            OutboxEvent(
                id=row.id,
                event_type=row.event_type,
                payload=row.payload,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def mark_published(self, session: AsyncSession, event_id: int) -> None:
        stmt = select(OutboxModel).where(OutboxModel.id == event_id)
        result = await session.execute(stmt)
        row = result.scalar_one()
        row.status = OutboxStatus.PUBLISHED
        row.published_at = datetime.now(UTC)
