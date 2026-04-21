from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from payments.get_payment.repository import GetPaymentRepository
from payments.shared.exceptions import PaymentNotFoundError
from payments.shared.models import PaymentModel


class GetPaymentService:
    def __init__(self, repository: GetPaymentRepository) -> None:
        self._repository = repository

    async def execute(self, session: AsyncSession, payment_id: UUID) -> PaymentModel:
        payment = await self._repository.get_by_id(session, payment_id)
        if payment is None:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        return payment


def get_get_payment_service() -> GetPaymentService:
    return GetPaymentService(repository=GetPaymentRepository())
