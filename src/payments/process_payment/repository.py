from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payments.shared.enums import PaymentStatus
from payments.shared.models import PaymentModel


class ProcessPaymentRepository:
    async def get_by_id(self, session: AsyncSession, payment_id: UUID) -> PaymentModel | None:
        stmt = select(PaymentModel).where(PaymentModel.id == payment_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_processed(
        self,
        session: AsyncSession,
        payment: PaymentModel,
        status: PaymentStatus,
        last_error: str | None = None,
    ) -> None:
        payment.status = status
        payment.last_error = last_error
        payment.processed_at = datetime.now(UTC)
