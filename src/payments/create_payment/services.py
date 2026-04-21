from sqlalchemy.ext.asyncio import AsyncSession

from payments.create_payment.repository import CreatePaymentRepository
from payments.create_payment.schemas import CreatePaymentRequest
from payments.shared.models import PaymentModel


class CreatePaymentService:
    def __init__(self, repository: CreatePaymentRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        session: AsyncSession,
        payload: CreatePaymentRequest,
        idempotency_key: str,
    ) -> PaymentModel:
        existing = await self._repository.get_by_idempotency_key(session, idempotency_key)
        if existing is not None:
            return existing
        return await self._repository.create_with_outbox(session, payload, idempotency_key)


def get_create_payment_service() -> CreatePaymentService:
    return CreatePaymentService(repository=CreatePaymentRepository())
