from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payments.shared.models import PaymentModel


class GetPaymentRepository:
    async def get_by_id(self, session: AsyncSession, payment_id: UUID) -> PaymentModel | None:
        stmt = select(PaymentModel).where(PaymentModel.id == payment_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
